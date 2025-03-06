# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import atexit
import typing
from ctypes import WinError
from fnmatch import fnmatch
from typing import Dict, List, Type

import addonHandler
import api
import braille
import config
import globalPluginHandler
import gui
import versionInfo
from logHandler import log
from NVDAObjects import NVDAObject
from utils.security import isRunningOnSecureDesktop, post_sessionLockStateChanged

from . import directoryChanges, handlers, settingsPanel
from .objects import findExtraOverlayClasses
from .secureDesktopHandling import SecureDesktopHandler
from .synthDetect import _SynthDetector

if typing.TYPE_CHECKING:
	from ...lib import (
		configuration,
		detection,
		ioThreadEx,
		namedPipe,
		protocol,
		rdPipe,
		secureDesktop,
	)
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	detection = addon.loadModule("lib.detection")
	ioThreadEx = addon.loadModule("lib.ioThreadEx")
	namedPipe = addon.loadModule("lib.namedPipe")
	protocol = addon.loadModule("lib.protocol")
	rdPipe = addon.loadModule("lib.rdPipe")
	secureDesktop = addon.loadModule("lib.secureDesktop")

supportsBrailleAutoDetectRegistration = (
	versionInfo.version_year,
	versionInfo.version_major,
) >= (2023, 3)


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):
	_synthDetector: _SynthDetector | None = None
	_ioThread: ioThreadEx.IoThreadEx | None = None

	def chooseNVDAObjectOverlayClasses(self, obj: NVDAObject, clsList: list[type[NVDAObject]]):
		findExtraOverlayClasses(obj, clsList)

	@classmethod
	def _updateRegistryForRdPipe(cls, install: bool, rdp: bool, citrix: bool) -> bool:
		if isRunningOnSecureDesktop():
			return False
		if citrix and not rdPipe.isCitrixSupported():
			citrix = False
		if not rdp and not citrix:
			return False
		if rdPipe.DEFAULT_ARCHITECTURE == rdPipe.Architecture.X86:
			return rdPipe.dllInstall(
				install=install,
				comServer=True,
				rdp=rdp,
				citrix=citrix,
			)
		else:
			res = False
			if rdp:
				if rdPipe.dllInstall(
					install=install,
					comServer=True,
					rdp=True,
					citrix=False,
				):
					res = True
			if citrix:
				if rdPipe.dllInstall(
					install=install,
					comServer=True,
					rdp=False,
					citrix=True,
					architecture=rdPipe.Architecture.X86,
				):
					res = True
		return res

	@classmethod
	def _registerRdPipeInRegistry(cls):
		persistent = config.isInstalledCopy() and configuration.getPersistentRegistration()
		rdp = configuration.getRemoteDesktopSupport()
		citrix = configuration.getCitrixSupport()
		if cls._updateRegistryForRdPipe(True, rdp, citrix) and not persistent:
			atexit.register(cls._unregisterRdPipeFromRegistry)

	def initializeOperatingModeServer(self):
		if configuration.getRecoverRemoteSpeech():
			self._synthDetector = _SynthDetector()
		if not supportsBrailleAutoDetectRegistration:
			detection.register()
		self._triggerBackgroundDetectRescan(
			rescanBraille=not supportsBrailleAutoDetectRegistration, force=True
		)
		if not isRunningOnSecureDesktop():
			post_sessionLockStateChanged.register(self._handleLockStateChanged)

	def initializeOperatingModeCommonClient(self):
		if isRunningOnSecureDesktop():
			return
		self._ioThread = ioThreadEx.IoThreadEx()
		self._ioThread.start()

	def initializeOperatingModeRdClient(self):
		if isRunningOnSecureDesktop():
			return
		self._registerRdPipeInRegistry()
		self._handlers: dict[str, handlers.RemoteHandler] = {}
		self._pipeWatcher = directoryChanges.DirectoryWatcher(
			namedPipe.PIPE_DIRECTORY,
			directoryChanges.FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME,
		)
		self._pipeWatcher.directoryChanged.register(self._handleNewPipe)
		self._pipeWatcher.start()
		self._initializeExistingPipes()

	def initializeOperatingModeSecureDesktop(self):
		if isRunningOnSecureDesktop():
			return
		secureDesktop.post_secureDesktopStateChange.register(self._handleSecureDesktop)
		self._sdHandler: SecureDesktopHandler | None = None

	def __init__(self):
		super().__init__()
		configuration.initializeConfig()
		configuredOperatingMode = configuration.getOperatingMode()
		if (
			configuredOperatingMode & configuration.OperatingMode.CLIENT
			or configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
		):
			self.initializeOperatingModeCommonClient()
		if configuredOperatingMode & configuration.OperatingMode.CLIENT:
			self.initializeOperatingModeRdClient()
		if configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP:
			self.initializeOperatingModeSecureDesktop()
		if configuredOperatingMode & configuration.OperatingMode.SERVER or (
			configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
			and isRunningOnSecureDesktop()
		):
			self.initializeOperatingModeServer()
		if isRunningOnSecureDesktop():
			return
		config.post_configProfileSwitch.register(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(
			settingsPanel.RemoteDesktopSettingsPanel
		)
		settingsPanel.RemoteDesktopSettingsPanel.post_onSave.register(self._handlePostConfigProfileSwitch)

	def _initializeExistingPipes(self):
		for match in namedPipe.getRdPipeNamedPipes():
			self._handleNewPipe(directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED, match)

	def _handleNewPipe(self, action: directoryChanges.FileNotifyInformationAction, fileName: str):
		if not fnmatch(fileName, namedPipe.RD_PIPE_GLOB_PATTERN):
			return
		if action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED:
			if fnmatch(
				fileName,
				namedPipe.RD_PIPE_GLOB_PATTERN.replace("*", f"{protocol.DriverType.BRAILLE.name}*"),
			):
				HandlerClass = handlers.RemoteBrailleHandler
			elif fnmatch(
				fileName,
				namedPipe.RD_PIPE_GLOB_PATTERN.replace("*", f"{protocol.DriverType.SPEECH.name}*"),
			):
				HandlerClass = handlers.RemoteSpeechHandler
			else:
				raise RuntimeError(f"Unknown named pipe: {fileName}")
			log.debug(f"Creating {HandlerClass.__name__} for {fileName!r}")
			handler = HandlerClass(self._ioThread, fileName)
			handler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
			handler.event_gainFocus(api.getFocusObject())
			self._handlers[fileName] = handler
		elif action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_REMOVED:
			log.debug(f"Pipe with name {fileName!r} removed")
			handler = self._handlers.pop(fileName, None)
			if handler:
				log.debug(f"Terminating handler {handler!r} for Pipe with name {fileName!r}")
				handler.decide_remoteDisconnect.unregister(self._handleRemoteDisconnect)
				handler.terminate()

	def terminateOperatingModeServer(self):
		if not isRunningOnSecureDesktop():
			post_sessionLockStateChanged.unregister(self._handleLockStateChanged)
		if not supportsBrailleAutoDetectRegistration:
			detection.unregister()
		if self._synthDetector:
			self._synthDetector.terminate()

	def terminateOperatingModeRdClient(self):
		if isRunningOnSecureDesktop():
			return
		if self._pipeWatcher:
			self._pipeWatcher.stop()
			self._pipeWatcher = None
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		if not configuration.getPersistentRegistration():
			self._unregisterRdPipeFromRegistry()

	def terminateOperatingModeCommonClient(self):
		if isRunningOnSecureDesktop():
			return
		if self._ioThread:
			self._ioThread.stop()
			self._ioThread = None

	def terminateOperatingModeSecureDesktop(self):
		if isRunningOnSecureDesktop():
			return
		secureDesktop.post_secureDesktopStateChange.unregister(self._handleSecureDesktop)
		self._handleSecureDesktop(False)

	@classmethod
	def _unregisterRdPipeFromRegistry(cls) -> bool:
		atexit.unregister(cls._unregisterRdPipeFromRegistry)
		rdp = configuration.getRemoteDesktopSupport()
		citrix = configuration.getCitrixSupport()
		return cls._updateRegistryForRdPipe(False, rdp, citrix)

	def terminate(self):
		try:
			if not isRunningOnSecureDesktop():
				settingsPanel.RemoteDesktopSettingsPanel.post_onSave.unregister(
					self._handlePostConfigProfileSwitch
				)
				gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
					settingsPanel.RemoteDesktopSettingsPanel
				)
				config.post_configProfileSwitch.unregister(self._handlePostConfigProfileSwitch)
			configuredOperatingMode = configuration.getOperatingMode()
			if configuredOperatingMode & configuration.OperatingMode.SERVER or (
				configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
				and isRunningOnSecureDesktop()
			):
				self.terminateOperatingModeServer()
			if configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP:
				self.terminateOperatingModeSecureDesktop()
			if configuredOperatingMode & configuration.OperatingMode.CLIENT:
				self.terminateOperatingModeRdClient()
			if (
				configuredOperatingMode & configuration.OperatingMode.CLIENT
				or configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
			):
				self.terminateOperatingModeCommonClient()
		finally:
			super().terminate()

	def _handlePostConfigProfileSwitch(self):  # NOQA: C901
		oldOperatingMode = configuration.getOperatingMode(True)
		newOperatingMode = configuration.getOperatingMode(False)
		oldClient = oldOperatingMode & configuration.OperatingMode.CLIENT
		newClient = newOperatingMode & configuration.OperatingMode.CLIENT
		oldServer = oldOperatingMode & configuration.OperatingMode.SERVER
		newServer = newOperatingMode & configuration.OperatingMode.SERVER
		oldSecureDesktop = oldOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
		newSecureDesktop = newOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
		oldSecureDesktopOrServer = (oldSecureDesktop and isRunningOnSecureDesktop()) or oldServer
		newSecureDesktopOrServer = (newSecureDesktop and isRunningOnSecureDesktop()) or newServer
		oldSecureDesktopOrClient = (oldSecureDesktop and not isRunningOnSecureDesktop()) or oldClient
		newSecureDesktopOrClient = (newSecureDesktop and not isRunningOnSecureDesktop()) or newClient
		if oldSecureDesktopOrServer and not newSecureDesktopOrServer:
			self.terminateOperatingModeServer()
		elif not oldSecureDesktopOrServer and newSecureDesktopOrServer:
			self.initializeOperatingModeServer()
		elif newSecureDesktopOrServer:
			oldRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(True)
			newRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(False)
			if oldRecoverRemoteSpeech is not newRecoverRemoteSpeech:
				if newRecoverRemoteSpeech:
					self._synthDetector = _SynthDetector()
					self._synthDetector._queueBgScan()
				elif self._synthDetector:
					self._synthDetector.terminate()
					self._synthDetector = None
		if oldSecureDesktop and not newSecureDesktop:
			self.terminateOperatingModeSecureDesktop()
		elif not oldSecureDesktop and newSecureDesktop:
			self.initializeOperatingModeSecureDesktop()
		if oldClient and not newClient:
			self.terminateOperatingModeRdClient()
		elif not oldClient and newClient:
			self.initializeOperatingModeRdClient()
		elif newClient:
			oldDriverSettingsManagement = configuration.getDriverSettingsManagement(True)
			newDriverSettingsManagement = configuration.getDriverSettingsManagement(False)
			if oldDriverSettingsManagement is not newDriverSettingsManagement:
				for handler in self._handlers.values():
					handler._handleDriverChanged(handler._driver)
			oldRdp = configuration.getRemoteDesktopSupport(True)
			newRdp = configuration.getRemoteDesktopSupport(False)
			if oldRdp is not newRdp:
				self._updateRegistryForRdPipe(newRdp, True, False)
			oldCitrix = configuration.getCitrixSupport(True)
			newCitrix = configuration.getCitrixSupport(False)
			if oldCitrix is not newCitrix:
				self._updateRegistryForRdPipe(newCitrix, False, True)
		if oldSecureDesktopOrClient and not newSecureDesktopOrClient:
			self.terminateOperatingModeCommonClient()
		elif not oldSecureDesktopOrClient and newSecureDesktopOrClient:
			self.initializeOperatingModeCommonClient()
		configuration.updateConfigCache()

	def _handleLockStateChanged(self, isNowLocked):
		if not isNowLocked:
			self._triggerBackgroundDetectRescan(force=True)

	def _triggerBackgroundDetectRescan(
		self, rescanSpeech: bool = True, rescanBraille: bool = True, force: bool = False
	):
		if rescanSpeech and self._synthDetector:
			self._synthDetector.rescan(force)
		detector = braille.handler._detector
		if rescanBraille and detector is not None:
			detector.rescan(
				usb=detector._detectUsb,
				bluetooth=detector._detectBluetooth,
				limitToDevices=detector._limitToDevices,
			)

	def _handleRemoteDisconnect(self, handler: handlers.RemoteHandler, error: int) -> bool:
		if isinstance(WinError(error), BrokenPipeError):
			handler.terminate()
			if handler._dev.pipeName in self._handlers:
				del self._handlers[handler._dev.pipeName]
			return True
		return False

	def event_gainFocus(self, obj, nextHandler):
		configuredOperatingMode = configuration.getOperatingMode()
		if not isRunningOnSecureDesktop():
			if configuredOperatingMode & configuration.OperatingMode.CLIENT:
				for handler in self._handlers.values():
					try:
						handler.event_gainFocus(obj)
					except Exception:
						log.error("Error calling event_gainFocus on handler", exc_info=True)
						continue
			if (
				configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP
				and not secureDesktop.hasSecureDesktopExtensionPoint
			):
				from IAccessibleHandler import SecureDesktopNVDAObject

				if isinstance(obj, SecureDesktopNVDAObject):
					secureDesktop.post_secureDesktopStateChange.notify(isSecureDesktop=True)
				elif self._sdHandler:
					secureDesktop.post_secureDesktopStateChange.notify(isSecureDesktop=False)
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self._triggerBackgroundDetectRescan()
		nextHandler()

	def _handleSecureDesktop(self, isSecureDesktop: bool):
		if isSecureDesktop:
			self._sdHandler = SecureDesktopHandler(self._ioThread)
		elif self._sdHandler:
			self._sdHandler.terminate()
			self._sdHandler = None


GlobalPlugin = RDGlobalPlugin
