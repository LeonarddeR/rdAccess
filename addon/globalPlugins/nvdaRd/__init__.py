import os
import globalPluginHandler
import addonHandler
import hwIo
from . import directoryChanges, settingsPanel
import typing
from glob import glob
from fnmatch import fnmatch
from . import configuration, handlers
from typing import Dict, List, Type
from logHandler import log
from .synthDetect import _SynthDetector
from utils.security import post_sessionLockStateChanged
import braille
from ctypes import WinError
from NVDAObjects import NVDAObject
from NVDAObjects.IAccessible import IAccessible
from .objects import RemoteDesktopControl
import config
import gui
import api
import versionInfo
import bdDetect
import atexit

if typing.TYPE_CHECKING:
	from ...lib import detection
	from ...lib import namedPipe
	from ...lib import protocol
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")
	namedPipe = addon.loadModule("lib.namedPipe")
	protocol = addon.loadModule("lib.protocol")
	rdPipe = addon.loadModule("lib.rdPipe")


PIPE_DIRECTORY = "\\\\?\\pipe\\"
globPattern = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")

ERROR_INVALID_HANDLE = 0x6
ERROR_BROKEN_PIPE = 0x6d


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):
	_synthDetector: typing.Optional[_SynthDetector] = None
	_ioThread: typing.Optional[hwIo.ioThread.IoThread] = None

	def chooseNVDAObjectOverlayClasses(self, obj: NVDAObject, clsList: List[Type[NVDAObject]]):
		if not isinstance(obj, IAccessible):
			return
		if (
			obj.windowClassName == 'IHWindowClass'
			and obj.simpleParent
			and obj.simpleParent.simpleParent
			and obj.simpleParent.simpleParent.windowClassName == 'TscShellContainerClass'
		):
			clsList.append(RemoteDesktopControl)

	def initializeOperatingModeServer(self):
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			from .monkeyPatcher import MonkeyPatcher
			self._monkeyPatcher = MonkeyPatcher()
		else:
			bdDetect.scanForDevices.register(detection.bgScanRD)
			bdDetect.scanForDevices.moveToEnd(detection.bgScanRD)
		if configuration.getRecoverRemoteSpeech():
			self._synthDetector = _SynthDetector()
		self._triggerBackgroundDetectRescan()
		post_sessionLockStateChanged.register(self._handleLockStateChanged)

	@classmethod
	def _updateRegistryForRdPipe(cls, install, rdp, citrix):
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
			atexit.register(cls._unregisterRdPipeFromRegistry, undoregisterAtExit=False)

	def initializeOperatingModeClient(self):
		handlers.RemoteHandler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
		self._registerRdPipeInRegistry()
		self._handlers: Dict[str, handlers.RemoteHandler] = {}
		self._ioThread = hwIo.ioThread.IoThread()
		self._ioThread.start()
		self._pipeWatcher = directoryChanges.DirectoryWatcher(
			PIPE_DIRECTORY,
			directoryChanges.FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME
		)
		self._pipeWatcher.directoryChanged.register(self._handleNewPipe)
		self._pipeWatcher.start()
		self._initializeExistingPipes()

	def __init__(self):
		super().__init__()
		configuration.initializeConfig()
		config.post_configProfileSwitch.register(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(settingsPanel.NvdaRDSettingsPanel)
		settingsPanel.NvdaRDSettingsPanel.post_onSave.register(self._handlePostConfigProfileSwitch)
		configuredOperatingMode = configuration.getOperatingMode()
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.initializeOperatingModeServer()
		if configuredOperatingMode & configuration.OperatingMode.CLIENT:
			self.initializeOperatingModeClient()

	def _initializeExistingPipes(self):
		for match in glob(globPattern):
			self._handleNewPipe(directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED, match)

	def _handleNewPipe(self, action: directoryChanges.FileNotifyInformationAction, fileName: str):
		if not fnmatch(fileName, globPattern):
			return
		if action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED:
			if fnmatch(fileName, globPattern.replace("*", f"{protocol.DriverType.BRAILLE.name}*")):
				HandlerClass = handlers.RemoteBrailleHandler
			elif fnmatch(fileName, globPattern.replace("*", f"{protocol.DriverType.SPEECH.name}*")):
				HandlerClass = handlers.RemoteSpeechHandler
			else:
				raise RuntimeError(f"Unknown named pipe: {fileName}")
			log.debug(f"Creating {HandlerClass.__name__} for {fileName!r}")
			handler = HandlerClass(self._ioThread, fileName)
			handler.event_gainFocus(api.getFocusObject())
			self._handlers[fileName] = handler
		elif action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_REMOVED:
			log.debug(f"Pipe with name {fileName!r} removed")
			handler = self._handlers.pop(fileName, None)
			if handler:
				log.debug(f"Terminating handler {handler!r} for Pipe with name {fileName!r}")
				handler.terminate()

	def terminateOperatingModeServer(self):
		post_sessionLockStateChanged.unregister(self._handleLockStateChanged)
		if self._synthDetector:
			self._synthDetector.terminate()
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			del self._monkeyPatcher
		else:
			bdDetect.scanForDevices.unregister(detection.bgScanRD)

	def terminateOperatingModeClient(self):
		if self._pipeWatcher:
			self._pipeWatcher.stop()
			self._pipeWatcher = None
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		if self._ioThread:
			self._ioThread.stop()
			self._ioThread = None
		if not configuration.getPersistentRegistration():
			self._unregisterRdPipeFromRegistry()
		handlers.RemoteHandler.decide_remoteDisconnect.unregister(self._handleRemoteDisconnect)

	@classmethod
	def _unregisterRdPipeFromRegistry(cls, undoregisterAtExit: bool = True):
		atexit.unregister(cls._unregisterRdPipeFromRegistry)
		rdp = configuration.getRemoteDesktopSupport()
		citrix = configuration.getCitrixSupport()
		cls._updateRegistryForRdPipe(False, rdp, citrix)

	def terminate(self):
		configuredOperatingMode = configuration.getOperatingMode()
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.terminateOperatingModeServer()
		if configuredOperatingMode & configuration.OperatingMode.CLIENT:
			self.terminateOperatingModeClient()
		settingsPanel.NvdaRDSettingsPanel.post_onSave.unregister(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(settingsPanel.NvdaRDSettingsPanel)
		config.post_configProfileSwitch.unregister(self._handlePostConfigProfileSwitch)
		super().terminate()

	def _handlePostConfigProfileSwitch(self, ):
		oldOperatingMode = configuration.getOperatingMode(True)
		newOperatingMode = configuration.getOperatingMode(False)
		if (
			oldOperatingMode & configuration.OperatingMode.SERVER
			and not newOperatingMode & configuration.OperatingMode.SERVER
		):
			self.terminateOperatingModeServer()
		elif (
			not oldOperatingMode & configuration.OperatingMode.SERVER
			and newOperatingMode & configuration.OperatingMode.SERVER
		):
			self.initializeOperatingModeServer()
		else:
			oldRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(True)
			newRecoverRemoteSpeech = configuration.getRecoverRemoteSpeech(False)
			if oldRecoverRemoteSpeech is not newRecoverRemoteSpeech:
				if newRecoverRemoteSpeech:
					self._synthDetector = _SynthDetector()
					self._synthDetector._queueBgScan()
				elif self._synthDetector:
					self._synthDetector.terminate()
					self._synthDetector = None
		if (
			oldOperatingMode & configuration.OperatingMode.CLIENT
			and not newOperatingMode & configuration.OperatingMode.CLIENT
		):
			self.terminateOperatingModeClient()
		elif (
			not oldOperatingMode & configuration.OperatingMode.CLIENT
			and newOperatingMode & configuration.OperatingMode.CLIENT
		):
			self.initializeOperatingModeClient()
		else:
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
		if not isNowLocked:
			self._triggerBackgroundDetectRescan()

	def _triggerBackgroundDetectRescan(self):
		if self._synthDetector:
			self._synthDetector.rescan()
		if braille.handler._detector is not None:
			braille.handler._detector.rescan()

	def _handleRemoteDisconnect(self, handler: handlers.RemoteHandler, pipeName: str, error: int) -> bool:
		if isinstance(WinError(error), BrokenPipeError):
			handler.terminate()
			if pipeName in self._handlers:
				del self._handlers[pipeName]
			return True
		return False

	def event_gainFocus(self, obj, nextHandler):
		configuredOperatingMode = configuration.getOperatingMode()
		if configuredOperatingMode & configuration.OperatingMode.CLIENT:
			for handler in self._handlers.values():
				handler.event_gainFocus(obj)
		if configuredOperatingMode & configuration.OperatingMode.SERVER:
			self._triggerBackgroundDetectRescan()
		nextHandler()


GlobalPlugin = RDGlobalPlugin
