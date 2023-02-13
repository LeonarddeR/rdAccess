import os
import globalPluginHandler
import addonHandler
import hwIo
from . import directoryChanges
import typing
from glob import glob
from fnmatch import fnmatch
from . import handlers
from typing import Dict, List, Type
from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE
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
from .monkeyPatcher import MonkeyPatcher

if typing.TYPE_CHECKING:
	from ...lib import configuration
	from ...lib import dialogs
	from ...lib import namedPipe
	from ...lib import protocol
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	dialogs = addon.loadModule("lib.dialogs")
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
			self._monkeyPatcher = MonkeyPatcher()
		self._synthDetector = _SynthDetector()
		self._triggerBackgroundDetectRescan()
		post_sessionLockStateChanged.register(self._handleLockStateChanged)

	def initializeOperatingModeClient(self):
		handlers.RemoteHandler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
		isInLocalMachine = rdPipe.keyExists(HKEY_LOCAL_MACHINE)
		self._rdPipeAddedToRegistry = rdPipe.addToRegistry(
			HKEY_CURRENT_USER,
			persistent=False,
			channelNamesOnly=isInLocalMachine
		)
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
		self._configuredOperatingMode = configuration.OperatingMode(configuration.config.conf[configuration.CONFIG_SECTION_NAME][configuration.OPERATING_MODE_SETTING_NAME])
		config.post_configProfileSwitch.register(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(dialogs.NvdaRDSettingsPanel)
		dialogs.NvdaRDSettingsPanel.post_onSave.register(self._handlePostConfigProfileSwitch)
		if self._configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.initializeOperatingModeServer()
		if self._configuredOperatingMode & configuration.OperatingMode.CLIENT:
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
		self._synthDetector.terminate()
		if versionInfo.version_year == 2023 and versionInfo.version_major == 1:
			del self._monkeyPatcher

	def terminateOperatingModeClient(self):
		self._pipeWatcher.stop()
		self._pipeWatcher = None
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		self._ioThread.stop()
		self._ioThread = None
		rdPipe.deleteFromRegistry(HKEY_CURRENT_USER, self._rdPipeAddedToRegistry)
		handlers.RemoteHandler.decide_remoteDisconnect.unregister(self._handleRemoteDisconnect)

	def terminate(self):
		if self._configuredOperatingMode & configuration.OperatingMode.SERVER:
			self.terminateOperatingModeServer()
		if self._configuredOperatingMode & configuration.OperatingMode.CLIENT:
			self.terminateOperatingModeClient()
		dialogs.NvdaRDSettingsPanel.post_onSave.unregister(self._handlePostConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(dialogs.NvdaRDSettingsPanel)
		config.post_configProfileSwitch.unregister(self._handlePostConfigProfileSwitch)
		super().terminate()

	def _handlePostConfigProfileSwitch(self, ):
		oldoperatingMode = self._configuredOperatingMode
		newOperatingMode = self._configuredOperatingMode = configuration.OperatingMode(configuration.config.conf[configuration.CONFIG_SECTION_NAME][configuration.OPERATING_MODE_SETTING_NAME])
		if oldoperatingMode == newOperatingMode:
			return
		if (
			oldoperatingMode & configuration.OperatingMode.SERVER
			and not newOperatingMode & configuration.OperatingMode.SERVER
		):
			self.terminateOperatingModeServer()
		elif (
			not oldoperatingMode & configuration.OperatingMode.SERVER
			and newOperatingMode & configuration.OperatingMode.SERVER
		):
			self.initializeOperatingModeServer()
		if (
			oldoperatingMode & configuration.OperatingMode.CLIENT
			and not newOperatingMode & configuration.OperatingMode.CLIENT
		):
			self.terminateOperatingModeClient()
		elif (
			not oldoperatingMode & configuration.OperatingMode.CLIENT
			and newOperatingMode & configuration.OperatingMode.CLIENT
		):
			self.initializeOperatingModeClient()

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
		if self._configuredOperatingMode & configuration.OperatingMode.CLIENT:
			for handler in self._handlers.values():
				handler.event_gainFocus(obj)
		if self._configuredOperatingMode & configuration.OperatingMode.SERVER:
			self._triggerBackgroundDetectRescan()
		nextHandler()


GlobalPlugin = RDGlobalPlugin
