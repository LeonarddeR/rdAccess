# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

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
from logHandler import log

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
	_terminating: bool = False

	def _handleRemoteDisconnect(self, handler: RemoteHandler, error: int) -> bool:
		if self._terminating:
			return True
		winErr = WinError(error)
		if isinstance(winErr, BrokenPipeError):
			log.warning(f"Handling remote disconnect of secure desktop handler {handler}: {winErr}")
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
		self._terminating = True
		self._speechHandler.terminate()
		braille.handler.display.loadSettings()
		self._brailleHandler.terminate()
		synthDriverHandler.getSynth().loadSettings()

	def _initializeHandler(self, handlerType: typing.Type[HandlerTypeT]) -> HandlerTypeT:
		sdId = f"NVDA_SD-{handlerType.driverType.name}"
		sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
		handler = handlerType(self._ioThreadRef(), sdPort, False)
		handler.decide_remoteDisconnect.register(self._handleRemoteDisconnect)
		return handler
