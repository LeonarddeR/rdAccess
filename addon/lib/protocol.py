import sys
import hwIo
from baseObject import AutoPropertyObject
import inspect
from enum import IntEnum
from typing import (
	Any,
	Callable,
	cast,
	Dict,
	Generic,
	TypeVar,
	Union,
)
from threading import Lock
import time
from logHandler import log
import pickle
import speech


SPEECH_INDEX_OFFSET = speech.manager.SpeechManager.MAX_INDEX + 1


class DriverType(IntEnum):
	SPEECH = ord(b'S')
	BRAILLE = ord(b'B')


class GenericCommand(IntEnum):
	ATTRIBUTE = ord(b'@')


class BrailleCommand(IntEnum):
	DISPLAY = ord(b'D')
	EXECUTE_GESTURE = ord(b'G')


class BrailleAttribute(IntEnum):
	NUM_CELLS = ord(b'C')
	GESTURE_MAP = ord(b'G')


class SpeechCommand(IntEnum):
	SPEAK = ord(b'S')
	CANCEL = ord(b'C')
	PAUSE = ord(b'P')
	INDEX_REACHED = ord(b'x')


class SpeechAttribute(IntEnum):
	SUPPORTED_COMMANDS = ord(b'C')
	SUPPORTED_SETTINGS = ord(b'S')
	LANGUAGE = ord(b'L')
	AVAILABLE_LANGUAGES = ord(b'l')
	RATE = ord(b'R')
	PITCH = ord(b'P')
	VOLUME = ord(b'o')
	INFLECTION = ord(b'I')
	VOICE = ord(b'V')
	AVAILABLE_VOICES = ord(b'v')
	VARIANT = ord(b'A')
	AVAILABLE_VARIANTS = ord(b'a')
	RATE_BOOST = ord(b'b')


AttributeValueT = TypeVar("AttributeValueT")
CommandT = Union[GenericCommand, SpeechCommand, BrailleCommand]
CommandHandlerT = Callable[[bytes], None]
AttributeT = Union[SpeechAttribute, BrailleAttribute]
attributeSenderT = Callable[..., None]
AttributeReceiverT = Callable[[bytes], AttributeValueT]


def commandHandler(command: CommandT):
	def wrapper(func: CommandHandlerT):
		func._command = command
		return func
	return wrapper


def attributeSender(attribute: AttributeT):
	def wrapper(func: attributeSenderT):
		func._sendingAttribute = attribute
		return func
	return wrapper


def attributeReceiver(attribute: AttributeT, defaultValue):
	def wrapper(func: AttributeReceiverT):
		func._receivingAttribute = attribute
		func._defaultValue = defaultValue
		return func
	return wrapper


class AttributeValueProcessor(Generic[AttributeValueT]):

	def __init__(self, attributeReceiver: AttributeReceiverT):
		self._attributeReceiver = attributeReceiver
		self._valueLock = Lock()
		self._valueLastSet: float = time.time()
		self._value: AttributeValueT = attributeReceiver._defaultValue

	def hasNewValueSince(self, t: float) -> bool:
		return t < self._valueLastSet

	@property
	def value(self) -> AttributeValueT:
		with self._valueLock:
			return self._value

	@value.setter
	def value(self, val: AttributeValueT):
		with self._valueLock:
			self._value = val

	def __call__(self, val: bytes):
		self.value = self._attributeReceiver(val)
		self._valueLastSet = time.time()


class RemoteProtocolHandler((AutoPropertyObject)):
	_dev: hwIo.IoBase
	_driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlers: Dict[CommandT, CommandHandlerT]
	_attributeSenders: Dict[AttributeT, attributeSenderT]
	_attributeValueProcessors: Dict[AttributeT, AttributeValueProcessor]

	def __init__(self, driverType: DriverType):
		self._driverType = driverType
		self._receiveBuffer = b""

	def _get__commandHandlers(self):
		handlers = inspect.getmembers(
			self.__class__,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_remoteCommand")
		)
		self._commandHandlers = {v._remoteCommand: getattr(self, k) for k, v in handlers}
		return self._commandHandlers

	def _get__attributeSenders(self):
		handlers = inspect.getmembers(
			self.__class__,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_sendingAttribute")
		)
		handlerDict: Dict[AttributeT, attributeSenderT] = {
			v._sendingAttribute: getattr(self, k)
			for k, v in handlers
		}
		self._attributeSenders = handlerDict
		return self._attributeSenders

	def _get__attributeValueProcessors(self):
		handlers = inspect.getmembers(
			self.__class__,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_receivingAttribute")
		)
		handlerDict: Dict[AttributeT, AttributeValueProcessor] = {
			v._receivingAttribute: AttributeValueProcessor(getattr(self, k))
			for k, v in handlers
		}
		self.__attributeValueProcessors = handlerDict
		return self._attributeValueProcessors

	def _onReceive(self, message: bytes):
		if self._receiveBuffer:
			message = self._receiveBuffer + message
		if not message[0] == self._driverType:
			raise RuntimeError(f"Unexpected payload: {message}")
		command = cast(CommandT, message[1])
		length = int.from_bytes(message[2:4], sys.byteorder)
		payload = message[4:]
		if length < len(payload):
			self._receiveBuffer = message
			return
		assert length == len(payload)
		handler = self._commandHandlers.get(command)
		if not handler:
			log.error(f"No handler for command {command}")
			return
		handler(payload)

	@commandHandler(GenericCommand.ATTRIBUTE)
	def _handleAttributeChanges(self, payload: bytes):
		attribute = cast(AttributeT, payload[0])
		value = payload[1:]
		if not value:
			handler = self._attributeSenders.get(attribute)
			if handler is None:
				log.error(f"No attribute sender for attribute {attribute}")
				return
			handler()
		else:
			handler = self._attributeValueProcessors.get(attribute)
			if handler is None:
				log.error(f"No attribute receiver for attribute {attribute}")
				return
			handler(value)

	def writeMessage(self, command: CommandT, payload: bytes = b""):
		data = bytes((
			self._driverType,
			command,
			*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
			*payload
		))
		return self._dev.write(data)

	def setRemoteAttribute(self, attribute: AttributeT, value: bytes):
		return self.writeMessage(GenericCommand.ATTRIBUTE, bytes((attribute, *value)))

	def getRemoteAttribute(self, attribute: AttributeT, timeout: float = 3.0):
		initialTime = time.time()
		handler = self._attributeValueProcessors.get(attribute)
		if not handler or not isinstance(handler, AttributeValueProcessor):
			raise RuntimeError(f"No attribute value processor for attribute {attribute}")
		self.writeMessage(GenericCommand.ATTRIBUTE, bytes((attribute,)))
		while timeout > 0.0:
			curTime = time.time()
			res: bool = self._dev.waitForRead(timeout=timeout)
			if res is False:
				timeout = 0.0
				continue
			if handler.hasNewValueSince(initialTime):
				return handler.value
			timeout -= (time.time() - curTime)
		else:
			raise TimeoutError(f"Wait for remote attribute {attribute} timed oud")

	def pickle(self, obj: Any):
		return pickle.dumps(obj, protocol=4)

	def unpickle(self, payload: bytes) -> Any:
		return pickle.loads(payload)
