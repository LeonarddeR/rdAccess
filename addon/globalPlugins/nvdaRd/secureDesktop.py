from .handlers import RemoteBrailleHandler, RemoteSpeechHandler
from .handlers._remoteHandler import RemoteHandler
import typing
from baseObject import AutoPropertyObject
import addonHandler
from hwIo import bgThread
import os.path

if typing.TYPE_CHECKING:
	from ...lib import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	namedPipe = addon.loadModule("lib.namedPipe")


HandlerTypeT = typing.TypeVar("HandlerTypeT", bound=RemoteHandler)


class SecureDesktopHandler(AutoPropertyObject):
	_brailleHandler: RemoteBrailleHandler
	_speechHandler: RemoteSpeechHandler

	def __init__(self):
		self._brailleHandler = self._initializeHandler(RemoteBrailleHandler)
		self._speechHandler = self._initializeHandler(RemoteSpeechHandler)

	def terminate(self):
		self._speechHandler.terminate()
		self._brailleHandler.terminate()

	@staticmethod
	def _initializeHandler(handlerType: typing.Type[HandlerTypeT]) -> HandlerTypeT:
		sdId = f"NVDA_SD-{handlerType.driverType.name}"
		sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
		return handlerType(bgThread, sdPort, False)
