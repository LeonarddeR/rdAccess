# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import atexit
import subprocess
import typing
from ctypes import WinError
from fnmatch import fnmatch

import addonHandler
import api
import braille
import config
import core
import globalPluginHandler
import gui
import inputCore
import keyboardHandler
import synthDriverHandler
import winUser
import wx
from hwIo import ioThread
from logHandler import log
from utils.security import isRunningOnSecureDesktop, post_sessionLockStateChanged
from winAPI.secureDesktop import post_secureDesktopStateChange

from . import directoryChanges, handlers, settingsPanel
from .synthDetect import SynthDetector

addon: addonHandler.Addon = addonHandler.getCodeAddon()

if typing.TYPE_CHECKING:
	from ...lib import (
		configuration,
		driver,
		namedPipe,
		nvdaCompat,
		protocol,
		rdPipe,
	)
else:
	configuration = addon.loadModule("lib.configuration")
	driver = addon.loadModule("lib.driver")
	namedPipe = addon.loadModule("lib.namedPipe")
	nvdaCompat = addon.loadModule("lib.nvdaCompat")
	protocol = addon.loadModule("lib.protocol")
	rdPipe = addon.loadModule("lib.rdPipe")

# Milliseconds between a caps lock gesture passing to the OS and reading the resulting toggle state.
CAPS_LOCK_PUSH_DELAY = 50


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):
	_synthDetector: SynthDetector | None = None
	_ioThread: ioThread.IoThread | None = None
	_capsLockPushPending: bool = False

	@classmethod
	def _updateRegistryForRdPipe(cls, install: bool, rdp: bool, citrix: bool) -> bool:
		if citrix and not rdPipe.isCitrixSupported():
			citrix = False
		if not rdp and not citrix:
			return False
		if rdPipe.defaultArchitecture == rdPipe.Architecture.X86:
			try:
				rdPipe.dllInstall(
					install=install,
					comServer=True,
					rdp=rdp,
					citrix=citrix,
				)
				return True
			except subprocess.CalledProcessError:
				log.exception()
				return False
		else:
			res = False
			if rdp:
				try:
					rdPipe.dllInstall(
						install=install,
						comServer=True,
						rdp=True,
						citrix=False,
					)
					res = True
				except subprocess.CalledProcessError:
					log.exception()
			if citrix:
				try:
					rdPipe.dllInstall(
						install=install,
						comServer=True,
						rdp=False,
						citrix=True,
						architecture=rdPipe.Architecture.X86,
					)
					res = True
				except subprocess.CalledProcessError:
					log.exception()
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
			self._synthDetector = SynthDetector()
		self._triggerBackgroundDetectRescan(
			rescanBraille=False,
			force=True,
		)
		if not isRunningOnSecureDesktop():
			post_sessionLockStateChanged.register(self._handleLockStateChanged)
			post_secureDesktopStateChange.register(self._handlePossibleServerDisconnect)
			inputCore.decide_executeGesture.register(self._detectCapsLockToggle)

	def initializeOperatingModeClient(self):
		self._ioThread = ioThread.IoThread()
		self._ioThread.start()
		wx.CallAfter(self._registerRdPipeInRegistry)
		self._handlers: dict[str, handlers.RemoteHandler] = {}
		self._detachedPipeNames: set[str] = set()
		self._failedPipeNames: set[str] = set()
		self._pipeWatcher = directoryChanges.DirectoryWatcher(
			namedPipe.PIPE_DIRECTORY,
			directoryChanges.FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME,
		)
		self._pipeWatcher.directoryChanged.register(self._reconcilePipes)
		self._pipeWatcher.start()
		self._reconcilePipes()
		if nvdaCompat.CAPS_LOCK_SYNC_SUPPORTED:
			inputCore.decide_handleRawKey.register(self._vetoInjectedCapsLock)

	def __init__(self):
		super().__init__()
		if isRunningOnSecureDesktop():
			return
		log.info(f"Initializing {addon.name} version {addon.version}")
		configuration.initializeConfig()
		configuredOperatingMode = configuration.getOperatingMode()
		if configuredOperatingMode & configuration.OperatingMode.CLIENT:
			self.initializeOperatingModeClient()
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.initializeOperatingModeServer()
		config.post_configProfileSwitch.register(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(
			settingsPanel.RemoteDesktopSettingsPanel,
		)
		settingsPanel.RemoteDesktopSettingsPanel.post_onSave.register(
			self._handlePostConfigProfileSwitch,
		)

	def _reconcilePipes(self):
		"""Aligns the handler map with the pipes that currently exist.

		Directory change notifications only signal that something changed; on the
		pipe file system events can be dropped by the kernel, so the actual pipe
		list is always re-globbed and diffed against the live handlers.
		"""
		currentPipes = set(namedPipe.getRdPipeNamedPipes())
		self._detachedPipeNames &= currentPipes
		self._failedPipeNames &= currentPipes
		for fileName in currentPipes - self._handlers.keys() - self._detachedPipeNames:
			try:
				self._createHandler(fileName)
			except Exception:
				if fileName not in self._failedPipeNames:
					self._failedPipeNames.add(fileName)
					log.debugWarning(f"Error creating handler for pipe {fileName!r}", exc_info=True)
		for fileName in list(self._handlers.keys() - currentPipes):
			handler = self._handlers.pop(fileName)
			log.debug(f"Pipe with name {fileName!r} removed, terminating handler {handler!r}")
			handler.decide_remoteDisconnect.unregister(self._handleRemoteDisconnect)
			handler.terminate()

	def _createHandler(self, fileName: str):
		if fnmatch(
			fileName,
			namedPipe.RD_PIPE_GLOB_PATTERN.replace(
				"*",
				f"{protocol.DriverType.BRAILLE.name}*",
			),
		):
			HandlerClass = handlers.RemoteBrailleHandler
		elif fnmatch(
			fileName,
			namedPipe.RD_PIPE_GLOB_PATTERN.replace(
				"*",
				f"{protocol.DriverType.SPEECH.name}*",
			),
		):
			HandlerClass = handlers.RemoteSpeechHandler
		else:
			raise RuntimeError(f"Unknown named pipe: {fileName}")
		log.debug(f"Creating {HandlerClass.__name__} for {fileName!r}")
		assert self._ioThread is not None
		handler = HandlerClass(self._ioThread, fileName)
		handler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
		handler.event_gainFocus(api.getFocusObject())
		self._handlers[fileName] = handler

	def terminateOperatingModeServer(self):
		inputCore.decide_executeGesture.unregister(self._detectCapsLockToggle)
		post_secureDesktopStateChange.unregister(self._handlePossibleServerDisconnect)
		post_sessionLockStateChanged.unregister(self._handleLockStateChanged)
		if self._synthDetector:
			self._synthDetector.terminate()

	def terminateOperatingModeClient(self):
		inputCore.decide_handleRawKey.unregister(self._vetoInjectedCapsLock)
		if self._pipeWatcher:
			self._pipeWatcher.stop()
			self._pipeWatcher = None
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		self._detachedPipeNames.clear()
		self._failedPipeNames.clear()
		if not configuration.getPersistentRegistration():
			self._unregisterRdPipeFromRegistry()
		if self._ioThread:
			self._ioThread.stop()
			self._ioThread = None

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
					self._handlePostConfigProfileSwitch,
				)
				gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
					settingsPanel.RemoteDesktopSettingsPanel,
				)
				config.post_configProfileSwitch.unregister(
					self._handlePostConfigProfileSwitch,
				)
			configuredOperatingMode = configuration.getOperatingMode()
			if configuredOperatingMode & configuration.OperatingMode.SERVER:
				self.terminateOperatingModeServer()
			if configuredOperatingMode & configuration.OperatingMode.CLIENT:
				self.terminateOperatingModeClient()
		finally:
			super().terminate()

	def _handlePostConfigProfileSwitch(self):
		oldOperatingMode = configuration.getOperatingMode(True)
		newOperatingMode = configuration.getOperatingMode(False)
		oldClient = oldOperatingMode & configuration.OperatingMode.CLIENT
		newClient = newOperatingMode & configuration.OperatingMode.CLIENT
		oldServer = oldOperatingMode & configuration.OperatingMode.SERVER
		newServer = newOperatingMode & configuration.OperatingMode.SERVER
		if oldServer and not newServer:
			self.terminateOperatingModeServer()
		elif not oldServer and newServer:
			self.initializeOperatingModeServer()
		elif newServer:
			oldRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(True)
			newRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(False)
			if oldRecoverRemoteSpeech is not newRecoverRemoteSpeech:
				if newRecoverRemoteSpeech:
					self._synthDetector = SynthDetector()
					self._synthDetector._queueBgScan()
				elif self._synthDetector:
					self._synthDetector.terminate()
					self._synthDetector = None
		if oldClient and not newClient:
			self.terminateOperatingModeClient()
		elif not oldClient and newClient:
			self.initializeOperatingModeClient()
		elif newClient:
			oldDriverSettingsManagement = configuration.getDriverSettingsManagement(
				True,
			)
			newDriverSettingsManagement = configuration.getDriverSettingsManagement(
				False,
			)
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
		configuration.updateConfigCache()

	def _handleLockStateChanged(self, isNowLocked):
		self._handlePossibleServerDisconnect()
		if not isNowLocked:
			self._triggerBackgroundDetectRescan(force=True)

	def _handlePossibleServerDisconnect(self, **kwargs):  # noqa: ARG002
		for remoteDriver in self._getActiveRemoteServerDrivers():
			remoteDriver._handlePossibleSessionDisconnect()

	def _getActiveRemoteServerDrivers(self) -> typing.Iterator[driver.RemoteDriver]:
		if braille.handler is not None and isinstance(braille.handler.display, driver.RemoteDriver):
			yield braille.handler.display
		synth = synthDriverHandler.getSynth()
		if isinstance(synth, driver.RemoteDriver):
			yield synth

	def _triggerBackgroundDetectRescan(
		self,
		rescanSpeech: bool = True,
		rescanBraille: bool = True,
		force: bool = False,
	):
		if rescanSpeech and self._synthDetector:
			self._synthDetector.rescan(force)
		assert braille.handler is not None
		detector = braille.handler._detector
		if rescanBraille and detector is not None:
			detector.rescan(
				usb=detector._detectUsb,
				bluetooth=detector._detectBluetooth,
				limitToDevices=detector._limitToDevices,
			)

	def _handleRemoteDisconnect(
		self,
		handler: handlers.RemoteHandler,
		error: int,
	) -> bool:
		if isinstance(WinError(error), BrokenPipeError):
			pipeName = handler._dev.pipeName
			# A broken pipe also brings down the virtual channel, after which the
			# pipe itself disappears. Tombstone the name until that happens, so
			# reconciliation doesn't reattach to the dying pipe.
			self._detachedPipeNames.add(pipeName)
			handler.terminate()
			if pipeName in self._handlers:
				del self._handlers[pipeName]
			return True
		return False

	@staticmethod
	def _isCapsLockPassThroughGesture(
		gesture: inputCore.InputGesture,
	) -> typing.TypeGuard[keyboardHandler.KeyboardInputGesture]:
		"""Whether this is a caps lock gesture that NVDA passes to the OS, toggling caps lock.

		False for gestures where the key acts as the NVDA modifier and for emulated
		caps lock gestures.
		"""
		return (
			isinstance(gesture, keyboardHandler.KeyboardInputGesture)
			and gesture.vkCode == winUser.VK_CAPITAL
			and not gesture.isNVDAModifierKey  # ty: ignore[unresolved-attribute]
		)

	def _vetoInjectedCapsLock(self, vkCode: int, extended: bool, injected: bool) -> bool:
		"""Swallows caps lock key events that a focused remote desktop client feeds back into
		the system. Applies while caps lock is configured as an NVDA modifier key; key events
		injected by NVDA itself pass through.
		"""
		return not (
			vkCode == winUser.VK_CAPITAL
			and injected
			and not keyboardHandler.ignoreInjected
			and configuration.getSynchronizeCapsLock()
			and keyboardHandler.isNVDAModifierKey(vkCode, extended)
			and any(handler._remoteProcessHasFocus for handler in list(self._handlers.values()))
		)

	def _detectCapsLockToggle(self, gesture: inputCore.InputGesture) -> bool:
		"""Schedules a caps lock state push to connected clients when a gesture is about
		to toggle caps lock. Never vetoes the gesture. Pushes are coalesced across key
		repeats.
		"""
		if (
			self._isCapsLockPassThroughGesture(gesture)
			and configuration.getSynchronizeCapsLock()
			and not self._capsLockPushPending
		):
			self._capsLockPushPending = True
			core.callLater(CAPS_LOCK_PUSH_DELAY, self._pushCapsLockToggle)
		return True

	def _pushCapsLockToggle(self):
		self._capsLockPushPending = False
		for remoteDriver in self._getActiveRemoteServerDrivers():
			remoteDriver._pushCapsLockToggle()

	def event_gainFocus(self, obj, nextHandler):
		if not isRunningOnSecureDesktop():
			configuredOperatingMode = configuration.getOperatingMode()
			if configuredOperatingMode & configuration.OperatingMode.CLIENT:
				for handler in self._handlers.values():
					try:
						handler.event_gainFocus(obj)
					except Exception:
						log.error("Error calling event_gainFocus on handler", exc_info=True)
						continue
			if configuredOperatingMode & configuration.OperatingMode.SERVER:
				self._triggerBackgroundDetectRescan()
		nextHandler()


GlobalPlugin = RDGlobalPlugin
