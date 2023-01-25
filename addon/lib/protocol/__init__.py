import sys
import hwIo
from baseObject import AutoPropertyObject
import inspect
from enum import IntEnum, Enum
from typing import (
	Any,
	Callable,
	cast,
	DefaultDict,
	Dict,
	Generic,
	TypeVar,
	Union,
)
from threading import Lock
import time
from logHandler import log
import pickle
from functools import wraps
import queueHandler
from .speech import SpeechAttribute, SpeechCommand
from .braille import BrailleAttribute, BrailleCommand
from typing_extensions import ParamSpec
from fnmatch import fnmatch


handlerParamSpec = ParamSpec("handlerParamSpec")


class DriverType(IntEnum):
	SPEECH = ord(b'S')
	BRAILLE = ord(b'B')


class GenericCommand(IntEnum):
	ATTRIBUTE = ord(b'@')
	INTERCEPT_GESTURE = ord(b'I')


class GenericAttribute(bytes, Enum):
	HAS_FOCUS = b"hasFocus"


RemoteProtocolHandlerT = TypeVar("RemoteProtocolHandlerT", bound="RemoteProtocolHandler")
AttributeValueT = TypeVar("AttributeValueT")
CommandT = Union[GenericCommand, SpeechCommand, BrailleCommand]
CommandHandlerUnboundT = Callable[[RemoteProtocolHandlerT, bytes], None]
CommandHandlerT = Callable[[bytes], None]
AttributeT = Union[GenericAttribute, SpeechAttribute, BrailleAttribute, bytes]
attributeFetcherT = Callable[..., bytes]
attributeSenderT = Callable[..., None]
AttributeReceiverT = Callable[[bytes], AttributeValueT]
AttributeReceiverUnboundT = Callable[[RemoteProtocolHandlerT, bytes], AttributeValueT]
WildCardAttributeReceiverT = Callable[[bytes, bytes], AttributeValueT]
WildCardAttributeReceiverUnboundT = Callable[[RemoteProtocolHandlerT, bytes, bytes], AttributeValueT]


def commandHandler(command: CommandT):
	def wrapper(func: CommandHandlerUnboundT):
		@wraps(func)
		def handler(self, payload: bytes):
			log.debug(f"Handling command {command}")
			return func(self, payload)
		handler._command = command
		return handler
	return wrapper


def attributeSender(attribute: AttributeT):
	def wrapper(func: attributeFetcherT):
		@wraps(func)
		def sender(
			self: "RemoteProtocolHandler",
			*args: handlerParamSpec.args,
			**kwargs: handlerParamSpec.kwargs
		) -> None:
			value = func(self, *args, **kwargs)
			self.setRemoteAttribute(attribute=attribute, value=value)
		sender._sendingAttribute = attribute
		return sender
	return wrapper


def attributeReceiver(attribute: AttributeT, defaultValue: AttributeValueT):
	def wrapper(func: AttributeReceiverUnboundT):
		func._receivingAttribute = attribute
		func._defaultValue = defaultValue
		return func
	return wrapper


class AttributeValueProcessor:
	_attributeReceivers: Dict[AttributeT, Union[AttributeReceiverT, WildCardAttributeReceiverT]]
	_valueLocks: DefaultDict[AttributeT, Lock]
	_valueTimes: DefaultDict[AttributeT, float]
	_values: Dict[AttributeT, Any]

	def __init__(self):
		self._attributeReceivers = {}
		self._valueLocks = DefaultDict(Lock)
		self._values = {}
		self._valueTimes = DefaultDict(time.time)

	def hasNewValueSince(self, attribute: AttributeT, t: float) -> bool:
		return t < self._valueTimes[attribute]

	def GetValue(self, attribute: AttributeT):
		with self._valueLocks[attribute]:
			return self._values[attribute]

	def SetValue(self, attribute: AttributeT, val):
		with self._valueLocks[attribute]:
			self._values[attribute] = val
			self._valueTimes[attribute] = time.time()

	def __call__(self, attribute: AttributeT, val: bytes):
		self.SetValue(attribute, self._attributeReceivers[attribute](val))


class RemoteProtocolHandler((AutoPropertyObject)):
	_dev: hwIo.IoBase
	driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlers: Dict[CommandT, CommandHandlerT]
	_attributeSenders: Dict[AttributeT, attributeSenderT]
	_attributeValueProcessors: Dict[AttributeT, AttributeValueProcessor]

	def __new__(cls, *args, **kwargs):
		self = super().__new__(cls, *args, **kwargs)
		commandHandlers = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_command")
		)
		self._commandHandlers = {v._command: getattr(self, k) for k, v in commandHandlers}
		senders = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_sendingAttribute")
		)
		self._attributeSenders = {
			v._sendingAttribute: getattr(self, k)
			for k, v in senders
		}
		receivers = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_receivingAttribute")
		)
		self._attributeValueProcessors = {
			v._receivingAttribute: AttributeValueProcessor(getattr(self, k))
			for k, v in receivers
		}
		return self

	def __init__(self):
		super().__init__()
		self._receiveBuffer = b""

	def _onReceive(self, message: bytes):
		if self._receiveBuffer:
			message = self._receiveBuffer + message
		if not message[0] == self.driverType:
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
		attribute, value = payload[1:].split(b'`', 1)
		if not value:
			match, handler = next(
				((k, v) for k, v in self._attributeSenders.items() if fnmatch(attribute, k)),
				(None, None)
			)
			if handler is None:
				log.error(f"No attribute sender for attribute {attribute}")
				return
			catchAll = b'*' in match
			if catchAll:
				handler(attribute)
			else:
				handler()
		else:
			handler = self._attributeValueProcessors.get(attribute)
			if handler is None:
				log.error(f"No attribute receiver for attribute {attribute}")
				return
			handler(value)

	def writeMessage(self, command: CommandT, payload: bytes = b""):
		data = bytes((
			self.driverType,
			command,
			*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
			*payload
		))
		return self._dev.write(data)

	def setRemoteAttribute(self, attribute: AttributeT, value: bytes):
		log.debug(f"Setting remote attribute {attribute!r}")
		return self.writeMessage(GenericCommand.ATTRIBUTE, bytes((attribute, *value)))

	def REQUESTRemoteAttribute(self, attribute: AttributeT):
		log.debug(f"Requesting remote attribute {attribute!r}")
		return self.writeMessage(GenericCommand.ATTRIBUTE, hwIo.intToByte(attribute))

	def _safeWait(self, predicate: Callable[[], bool], timeout: float = 3.0):
		while timeout > 0.0:
			if predicate():
				return True
			curTime = time.time()
			res: bool = self._dev.waitForRead(timeout=timeout)
			if res is False:
				break
			timeout -= (time.time() - curTime)
		return predicate()

	def getRemoteAttribute(self, attribute: AttributeT, timeout: float = 3.0):
		initialTime = time.time()
		handler = self._attributeValueProcessors.get(attribute)
		if not handler or not isinstance(handler, AttributeValueProcessor):
			raise RuntimeError(f"No attribute value processor for attribute {attribute}")
		self.REQUESTRemoteAttribute(attribute=attribute)
		if self._safeWait(lambda: handler.hasNewValueSince(initialTime), timeout=timeout):
			newValue = handler.value
			log.debug(f"Received new value {newValue!r} for remote attribute {attribute!r}")
			return newValue
		raise TimeoutError(f"Wait for remote attribute {attribute} timed out")

	def _pickle(self, obj: Any):
		return pickle.dumps(obj, protocol=4)

	def _unpickle(self, payload: bytes) -> Any:
		return pickle.loads(payload)

	def _queueFunctionOnMainThread(self, func, *args, **kwargs):
		queueHandler.queueFunction(queueHandler.eventQueue, func, *args, **kwargs)
