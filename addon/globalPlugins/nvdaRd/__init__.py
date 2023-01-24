import os
import globalPluginHandler
import addonHandler
import hwIo
from . import directoryChanges
import typing
from glob import glob
from fnmatch import fnmatch
from . import handlers
from typing import Dict
import bdDetect

if typing.TYPE_CHECKING:
	from ...lib import protocol
	from ...lib import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


PIPE_DIRECTORY = "\\\\?\\pipe\\"
globPattern = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super().__init__()
		self._handlers: Dict[str, handlers.RemoteHandler] = {}
		self._pipeWatcher = directoryChanges.DirectoryWatcher(
			PIPE_DIRECTORY,
			directoryChanges.FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME
		)
		self._pipeWatcher.directoryChanged.register(self._handleNewPipe)
		self._pipeWatcher.start(hwIo.bgThread)
		self._initializeExistingPipes()

	def _initializeExistingPipes(self):
		for match in glob(globPattern):
			self._handleNewPipe(directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED, match)

	def _handleNewPipe(self, action: directoryChanges.FileNotifyInformationAction, fileName: str):
		if not fnmatch(fileName, globPattern):
			return
		if action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_ADDED:
			if fnmatch(fileName, globPattern.replace("*", f"{protocol.DriverType.BRAILLE.name}*")):
				handler = handlers.RemoteBrailleHandler(fileName)
			elif fnmatch(fileName, globPattern.replace("*", f"{protocol.DriverType.SPEECH.name}*")):
				handler = handlers.RemoteSpeechHandler(fileName)
			else:
				raise RuntimeError(f"Unknown named pipe: {fileName}")
			self._handlers[fileName] = handler
		elif action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_REMOVED:
			handler = self._handlers.get(fileName, None)
			if handler:
				handler.terminate()
				del self._handlers[fileName]

	def terminate(self):
		self._pipeWatcher.stop()
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		super().terminate()

	def event_gainFocus(self, obj, nextHandler):
		for handler in self._handlers.values():
			handler.event_gainFocus(obj)
		nextHandler()


GlobalPlugin = RDGlobalPlugin
