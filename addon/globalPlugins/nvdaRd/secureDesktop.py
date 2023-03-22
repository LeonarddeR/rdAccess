from __future__ import annotations
from .handlers import RemoteBrailleHandler, RemoteSpeechHandler
from .handlers._remoteHandler import RemoteHandler
import typing
from baseObject import AutoPropertyObject
import addonHandler
from hwIo.ioThread import IoThread
import os.path
import braille
import synthDriverHandler
from ctypes import WinError
import weakref

if typing.TYPE_CHECKING:
	from ...lib import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	namedPipe = addon.loadModule("lib.namedPipe")


HandlerTypeT = typing.TypeVar("HandlerTypeT", bound=RemoteHandler)


class SecureDesktopHandler(AutoPropertyObject):
	_ioThreadRef: weakref.ReferenceType[IoThread]
	_brailleHandler: RemoteBrailleHandler
	_speechHandler: RemoteSpeechHandler

	def _handleRemoteDisconnect(self, handler: RemoteHandler, error: int) -> bool:
		if isinstance(WinError(error), BrokenPipeError):
			ioThread = self._ioThreadRef()
			pipeName = handler._dev.pipeName
			handler.terminate()
			handler.__init__(ioThread=ioThread, pipeName=pipeName, isNamedPipeClient=False)
			return True
		return False

	def __init__(self, ioThread: IoThread):
		self._ioThreadRef = weakref.ref(ioThread)
		braille.handler.display.saveSettings()
		self._brailleHandler = self._initializeHandler(RemoteBrailleHandler)
		synthDriverHandler.getSynth().saveSettings()
		self._speechHandler = self._initializeHandler(RemoteSpeechHandler)

	def terminate(self):
		self._speechHandler.terminate()
		braille.handler.display.loadSettings()
		self._brailleHandler.terminate()
		synthDriverHandler.getSynth().loadSettings()

	def _initializeHandler(self, handlerType: typing.Type[HandlerTypeT]) -> HandlerTypeT:
		sdId = f"NVDA_SD-{handlerType.driverType.name}"
		sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
		handler = handlerType(self._ioThreadRef(), sdPort, False)
		handler.hasFocus = handler._remoteProcessHasFocus = handler._remoteSessionhasFocus = True
		handler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
		return handler
