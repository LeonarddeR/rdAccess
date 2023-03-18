import globalPluginHandler
import addonHandler
import hwIo
from . import directoryChanges, settingsPanel
import typing
from fnmatch import fnmatch
from . import handlers
from typing import Dict, List, Type
from logHandler import log
from .synthDetect import _SynthDetector
from utils.security import post_sessionLockStateChanged
import braille
from ctypes import WinError
from NVDAObjects import NVDAObject
from .objects import findExtraOverlayClasses
import config
import gui
import api
import versionInfo
import bdDetect
import atexit
from systemUtils import _isSecureDesktop
from IAccessibleHandler import SecureDesktopNVDAObject
from .secureDesktop import SecureDesktopHandler

if typing.TYPE_CHECKING:
	from ...lib import configuration
	from ...lib import detection
	from ...lib import namedPipe
	from ...lib import protocol
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	detection = addon.loadModule("lib.detection")
	namedPipe = addon.loadModule("lib.namedPipe")
	protocol = addon.loadModule("lib.protocol")
	rdPipe = addon.loadModule("lib.rdPipe")


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):
	_synthDetector: typing.Optional[_SynthDetector] = None
	_ioThread: typing.Optional[hwIo.ioThread.IoThread] = None

	def chooseNVDAObjectOverlayClasses(self, obj: NVDAObject, clsList: List[Type[NVDAObject]]):
		findExtraOverlayClasses(obj, clsList)

	@classmethod
	def _updateRegistryForRdPipe(cls, install, rdp, citrix):
		if _isSecureDesktop():
			return
		if citrix and not rdPipe.isCitrixSupported():
			citrix = False
		if not rdp and not citrix:
			return
		if rdPipe.DEFAULT_ARCHITECTURE == rdPipe.Architecture.X86:
			rdPipe.dllInstall(
				install=install,
				comServer=True,
				rdp=rdp,
				citrix=citrix,
			)
		else:
			if rdp:
				rdPipe.dllInstall(
					install=install,
					comServer=True,
					rdp=True,
					citrix=False,
				)
			if citrix:
				rdPipe.dllInstall(
					install=install,
					comServer=True,
					rdp=False,
					citrix=True,
					architecture=rdPipe.Architecture.X86
				)

	@classmethod
	def _registerRdPipeInRegistry(cls):
		persistent = config.isInstalledCopy() and configuration.getPersistentRegistration()
		rdp = configuration.getRemoteDesktopSupport()
		citrix = configuration.getCitrixSupport()
		cls._updateRegistryForRdPipe(True, rdp, citrix)
		if not persistent:
			atexit.register(cls._unregisterRdPipeFromRegistry)

	def initializeOperatingModeServer(self):
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			self._monkeyPatcher.patchBdDetect()
		else:
			bdDetect.scanForDevices.register(detection.bgScanRD)
			bdDetect.scanForDevices.moveToEnd(detection.bgScanRD)
		if configuration.getRecoverRemoteSpeech():
			self._synthDetector = _SynthDetector()
		self._triggerBackgroundDetectRescan(True)
		if not _isSecureDesktop():
			post_sessionLockStateChanged.register(self._handleLockStateChanged)

	def initializeOperatingModeCommonClient(self):
		if _isSecureDesktop():
			return
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			self._monkeyPatcher.patchSynthDriverHandler()
		self._ioThread = hwIo.ioThread.IoThread()
		self._ioThread.start()

	def initializeOperatingModeRdClient(self):
		if _isSecureDesktop():
			return
		self._registerRdPipeInRegistry()
		self._handlers: Dict[str, handlers.RemoteHandler] = {}
		self._pipeWatcher = directoryChanges.DirectoryWatcher(
			namedPipe.PIPE_DIRECTORY,
			directoryChanges.FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME
		)
		self._pipeWatcher.directoryChanged.register(self._handleNewPipe)
		self._pipeWatcher.start()
		self._initializeExistingPipes()

	def initializeOperatingModeSecureDesktop(self):
		if _isSecureDesktop():
			return
		self._sdHandler: typing.Optional[SecureDesktopHandler] = None

	def __init__(self):
		super().__init__()
		configuration.initializeConfig()
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			from .monkeyPatcher import MonkeyPatcher
			self._monkeyPatcher = MonkeyPatcher()
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
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.initializeOperatingModeServer()
		if _isSecureDesktop():
			return
		config.post_configProfileSwitch.register(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(settingsPanel.NvdaRDSettingsPanel)
		settingsPanel.NvdaRDSettingsPanel.post_onSave.register(self._handlePostConfigProfileSwitch)

	def _initializeExistingPipes(self):
		for match in namedPipe.getRdPipeNamedPipes():
			self._handleNewPipe(directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED, match)

	def _handleNewPipe(self, action: directoryChanges.FileNotifyInformationAction, fileName: str):
		if not fnmatch(fileName, namedPipe.RD_PIPE_GLOB_PATTERN):
			return
		if action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED:
			if fnmatch(fileName, namedPipe.RD_PIPE_GLOB_PATTERN.replace("*", f"{protocol.DriverType.BRAILLE.name}*")):
				HandlerClass = handlers.RemoteBrailleHandler
			elif fnmatch(fileName, namedPipe.RD_PIPE_GLOB_PATTERN.replace("*", f"{protocol.DriverType.SPEECH.name}*")):
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
		if not _isSecureDesktop():
			post_sessionLockStateChanged.unregister(self._handleLockStateChanged)
		if self._synthDetector:
			self._synthDetector.terminate()
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			self._monkeyPatcher.unpatchBdDetect()
		else:
			bdDetect.scanForDevices.unregister(detection.bgScanRD)

	def terminateOperatingModeRdClient(self):
		if _isSecureDesktop():
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
		if _isSecureDesktop():
			return
		if self._ioThread:
			self._ioThread.stop()
			self._ioThread = None
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			self._monkeyPatcher.unpatchSynthDriverHandler()

	def terminateOperatingModeSecureDesktop(self):
		if _isSecureDesktop():
			return
		self._handleSecureDesktop(False)

	@classmethod
	def _unregisterRdPipeFromRegistry(cls):
		atexit.unregister(cls._unregisterRdPipeFromRegistry)
		rdp = configuration.getRemoteDesktopSupport()
		citrix = configuration.getCitrixSupport()
		cls._updateRegistryForRdPipe(False, rdp, citrix)

	def terminate(self):
		try:
			if not _isSecureDesktop():
				settingsPanel.NvdaRDSettingsPanel.post_onSave.unregister(self._handlePostConfigProfileSwitch)
				gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(settingsPanel.NvdaRDSettingsPanel)
				config.post_configProfileSwitch.unregister(self._handlePostConfigProfileSwitch)
			configuredOperatingMode = configuration.getOperatingMode()
			if configuredOperatingMode & configuration.OperatingMode.SERVER:
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
			if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
				del self._monkeyPatcher
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
		oldSecureDesktopOrServer = (oldSecureDesktop and _isSecureDesktop()) or oldServer
		newSecureDesktopOrServer = (newSecureDesktop and _isSecureDesktop()) or newServer
		oldSecureDesktopOrClient = (oldSecureDesktop and not _isSecureDesktop()) or oldClient
		newSecureDesktopOrClient = (newSecureDesktop and not _isSecureDesktop()) or newClient
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
			self._triggerBackgroundDetectRescan(True)

	def _triggerBackgroundDetectRescan(self, force: bool = False):
		if self._synthDetector:
			self._synthDetector.rescan(force)
		if braille.handler._detector is not None:
			braille.handler._detector.rescan()

	def _handleRemoteDisconnect(self, handler: handlers.RemoteHandler, error: int) -> bool:
		if isinstance(WinError(error), BrokenPipeError):
			handler.terminate()
			if handler._dev.pipeName in self._handlers:
				del self._handlers[handler._dev.pipeName]
			return True
		return False

	def event_gainFocus(self, obj, nextHandler):
		configuredOperatingMode = configuration.getOperatingMode()
		if not _isSecureDesktop():
			if configuredOperatingMode & configuration.OperatingMode.CLIENT:
				for handler in self._handlers.values():
					try:
						handler.event_gainFocus(obj)
					except Exception:
						log.error("Error calling event_gainFocus on handler", exc_info=True)
						continue
			if configuredOperatingMode & configuration.OperatingMode.SECURE_DESKTOP:
				if isinstance(obj, SecureDesktopNVDAObject):
					self._handleSecureDesktop(True)
				elif self._sdHandler:
					self._handleSecureDesktop(False)
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self._triggerBackgroundDetectRescan()
		nextHandler()

	def _handleSecureDesktop(self, state: bool):
		if state:
			self._sdHandler = SecureDesktopHandler(self._ioThread)
		elif self._sdHandler:
			self._sdHandler.terminate()
			self._sdHandler = None


GlobalPlugin = RDGlobalPlugin
