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
from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE
from logHandler import log

if typing.TYPE_CHECKING:
	from ...lib import protocol
	from ...lib import namedPipe
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")
	rdPipe = addon.loadModule("lib.rdPipe")


PIPE_DIRECTORY = "\\\\?\\pipe\\"
globPattern = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")


class RDGlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super().__init__()
		isInLocalMachine = rdPipe.keyExists(HKEY_LOCAL_MACHINE)
		self._rdPipeAddedToRegistry = rdPipe.addToRegistry(
			HKEY_CURRENT_USER,
			persistent=False,
			channelNamesOnly=isInLocalMachine
		)
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
				log.debug(f"Creating remote braille handler for {fileName!r}")
				handler = handlers.RemoteBrailleHandler(fileName)
			elif fnmatch(fileName, globPattern.replace("*", f"{protocol.DriverType.SPEECH.name}*")):
				log.debug(f"Creating remote speech handler for {fileName!r}")
				handler = handlers.RemoteSpeechHandler(fileName)
			else:
				raise RuntimeError(f"Unknown named pipe: {fileName}")
			self._handlers[fileName] = handler
		elif action == directoryChanges.FileNotifyInformationAction.FILE_ACTION_REMOVED:
			log.debug(f"Pipe with name {fileName!r} removed")
			handler = self._handlers.pop(fileName, None)
			if handler:
				log.debug(f"Terminating handler {handler!r} for Pipe with name {fileName!r}")
				handler.terminate()

	def terminate(self):
		self._pipeWatcher.stop()
		for handler in self._handlers.values():
			handler.terminate()
		self._handlers.clear()
		rdPipe.deleteFromRegistry(HKEY_CURRENT_USER, self._rdPipeAddedToRegistry)
		super().terminate()

	def event_gainFocus(self, obj, nextHandler):
		for handler in self._handlers.values():
			handler.event_gainFocus(obj)
		nextHandler()


GlobalPlugin = RDGlobalPlugin
