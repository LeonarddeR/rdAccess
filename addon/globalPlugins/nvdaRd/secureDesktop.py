from concurrent.futures import ThreadPoolExecutor
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
	_executor: ThreadPoolExecutor
	_brailleHandler: typing.Optional[RemoteBrailleHandler] = None
	_speechHandler: typing.Optional[RemoteSpeechHandler] = None

	def __init__(self):
		self._executor = ThreadPoolExecutor(2, self.__class__.__name__)
		self._executor.submit(self.initializeBrailleHandler)
		self._executor.submit(self.initializeSpeechHandler)

	def terminate(self):
		if self._speechHandler:
			self._speechHandler.terminate()
			self._speechHandler = None
		if self._brailleHandler:
			self._brailleHandler.terminate()
			self._brailleHandler = None
		self._executor.shutdown()

	@staticmethod
	def _initializeHandler(handlerType: typing.Type[HandlerTypeT]) -> HandlerTypeT:
		sdId = f"NVDA_SD-{handlerType.driverType.name}"
		sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
		return handlerType(bgThread, sdPort, False)

	def initializeBrailleHandler(self):
		self._brailleHandler = self._initializeHandler(RemoteBrailleHandler)

	def initializeSpeechHandler(self):
		self._speechHandler = self._initializeHandler(RemoteSpeechHandler)
