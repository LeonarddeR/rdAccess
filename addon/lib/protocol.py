import sys
import hwIo
from baseObject import AutoPropertyObject
import inspect
from enum import IntEnum
from typing import Union, Callable, Dict, TypeVar, Generic, cast, Any
from threading import Lock
import time
from logHandler import log
import pickle


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


AttributeValueType = TypeVar("AttributeValueType")
CommandType = Union[GenericCommand, SpeechCommand, BrailleCommand]
AttributeType = Union[SpeechAttribute, BrailleAttribute]


def commandHandler(command: CommandType):
	def wrapper(func):
		func._remoteCommand = command
		return func
	return wrapper


def attributeHandler(attribute: AttributeType, defaultValue=None):
	def wrapper(func):
		func._remoteAttribute = attribute
		func._defaultValue = defaultValue
		return func
	return wrapper


class AttributeValueProcessor(Generic[AttributeValueType]):

	def __init__(self, valueExtractor: Callable[[bytes], AttributeValueType]):
		self._valueExtractor = valueExtractor
		self._valueLock = Lock()
		self._valueLastSet: float = time.time()
		self._value: AttributeValueType = valueExtractor._defaultValue

	def hasNewValueSince(self, t: float) -> bool:
		return t < self._valueLastSet

	@property
	def value(self) -> AttributeValueType:
		with self._valueLock:
			return self._value

	@value.setter
	def value(self, val: AttributeValueType):
		with self._valueLock:
			self._value = val

	def __call__(self, val: bytes):
		self.value = self._valueExtractor(val)
		self._valueLastSet = time.time()


class RemoteProtocolHandler((AutoPropertyObject)):
	_dev: hwIo.IoBase
	_driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlers: Dict[CommandType, Callable[[bytes], None]]
	_attributeHandlers: Dict[AttributeType, Callable[[bytes], None]]

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

	def _get__attributeHandlers(self):
		handlers = inspect.getmembers(
			self.__class__,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_remoteAttribute")
		)
		handlerDict = {}
		for k, v in handlers:
			key = v._remoteAttribute
			callable = getattr(self, k)
			if callable._defaultValue is not None:
				callable = AttributeValueProcessor(callable)
			handlerDict[key] = callable
		self._attributeHandlers = handlerDict
		return self._attributeHandlers

	def _onReceive(self, message: bytes):
		if self._receiveBuffer:
			message = self._receiveBuffer + message
		if not message[0] == self._driverType:
			raise RuntimeError(f"Unexpected payload: {message}")
		command = cast(CommandType, message[1])
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
		attribute = cast(AttributeType, payload[0])
		handler = self._attributeHandlers.get(attribute)
		if handler is None:
			log.error(f"No attribute handler for attribute {attribute}")
			return
		handler(payload[1:])

	def writeMessage(self, command: CommandType, payload: bytes = b""):
		data = bytes((
			self._driverType,
			command,
			*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
			*payload
		))
		return self._dev.write(data)

	def setRemoteAttribute(self, attribute: AttributeType, value: bytes):
		return self.writeMessage(GenericCommand.ATTRIBUTE, bytes((attribute, *value)))

	def getRemoteAttribute(self, attribute: AttributeType, timeout: float = 3.0):
		initialTime = time.time()
		handler = self._attributeHandlers.get(attribute)
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
