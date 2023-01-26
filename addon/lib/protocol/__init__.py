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
	Optional,
	Set,
	Type,
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
from fnmatch import fnmatch
from functools import partial
from extensionPoints import HandlerRegistrar
import types


class DriverType(IntEnum):
	SPEECH = ord(b'S')
	BRAILLE = ord(b'B')


class GenericCommand(IntEnum):
	ATTRIBUTE = ord(b'@')
	INTERCEPT_GESTURE = ord(b'I')


class GenericAttribute(bytes, Enum):
	HAS_FOCUS = b"hasFocus"


AttributeValueT = TypeVar("AttributeValueT")
CommandT = Union[GenericCommand, SpeechCommand, BrailleCommand]
CommandHandlerUnboundT = Callable[["RemoteProtocolHandler", bytes], None]
CommandHandlerT = Callable[[bytes], None]
AttributeT = Union[GenericAttribute, SpeechAttribute, BrailleAttribute, bytes]
attributeFetcherT = Callable[..., bytes]
attributeSenderT = Callable[..., None]
AttributeReceiverT = Callable[[bytes], AttributeValueT]
AttributeReceiverUnboundT = Callable[["RemoteProtocolHandler", bytes], AttributeValueT]
WildCardAttributeReceiverT = Callable[[AttributeT, bytes], AttributeValueT]
WildCardAttributeReceiverUnboundT = Callable[["RemoteProtocolHandler", AttributeT, bytes], AttributeValueT]
AttributeHandlerT = TypeVar(
	"AttributeHandlerT",
	attributeFetcherT,
	AttributeReceiverUnboundT,
	WildCardAttributeReceiverUnboundT,
)


def commandHandler(command: CommandT):
	def wrapper(func: CommandHandlerUnboundT):
		@wraps(func)
		def handler(self, payload: bytes):
			log.debug(f"Handling command {command}")
			return func(self, payload)
		handler._command = command
		return handler
	return wrapper


class AttributeHandler(Generic[AttributeHandlerT]):
	_attribute: AttributeT = b''
	_func: AttributeHandlerT

	@property
	def _isCatchAll(self) -> bool:
		return b'*' in self._attribute

	def __init__(self, attribute: AttributeT, func: AttributeHandlerT):
		self._attribute = attribute
		self._func = func

	def __call__(
			self,
			protocolHandler: "RemoteProtocolHandler",
			attribute: AttributeT,
			*args,
			**kwargs
	):
		if self._isCatchAll:
			return self._func(protocolHandler, attribute, *args, **kwargs)
		else:
			return self._func(protocolHandler, *args, **kwargs)

	def __get__(self, obj, objtype=None):
		if obj is None:
			return self
		return types.MethodType(self, obj)


class AttributeSender(AttributeHandler[attributeFetcherT]):

	def __call__(self, protocolHandler: "RemoteProtocolHandler", attribute: AttributeT, *args, **kwargs):
		value = super().__call__(protocolHandler, attribute, *args, **kwargs)
		protocolHandler.setRemoteAttribute(attribute=attribute, value=value)


def attributeSender(attribute: AttributeT):
	return partial(AttributeSender, attribute)


class AttributeReceiver(
		AttributeHandler[Union[AttributeReceiverUnboundT, WildCardAttributeReceiverUnboundT]],
		Generic[AttributeValueT]
):
	_defaultValueGetter: Optional[Callable[["RemoteProtocolHandler", AttributeT], AttributeValueT]]

	def __init__(
			self,
			attribute: AttributeT,
			func: Union[AttributeReceiverUnboundT, WildCardAttributeReceiverUnboundT],
			defaultValueGetter: Optional[Callable[["RemoteProtocolHandler", AttributeT], AttributeValueT]]
	):
		super().__init__(attribute, func)
		self._defaultValueGetter = defaultValueGetter

	def defaultValueGetter(self, func: Callable[["RemoteProtocolHandler", AttributeT], AttributeValueT]):
		self._defaultValueGetter = func
		return func


def attributeReceiver(
		attribute: AttributeT,
		defaultValue: AttributeValueT = NotImplemented
):
	kwargs = {}
	if defaultValue is not NotImplemented:
		kwargs["defaultValueGetter"] = lambda self, attribute: defaultValue
	return partial(AttributeReceiver, attribute, **kwargs)


class AttributeHandlerStore(HandlerRegistrar):

	def _getHandler(self, attribute: AttributeT) -> AttributeHandler:
		handler = next(
			(v for v in self.handlers if fnmatch(attribute, v._attribute)),
			None
		)
		if handler is None:
			raise NotImplementedError(f"No attribute sender for attribute {attribute}")
		return handler


class AttributeSenderStore(AttributeHandlerStore):

	def __call__(self, attribute: AttributeT, *args, **kwargs):
		handler = self._getHandler(attribute)
		handler(attribute, *args, **kwargs)


class AttributeValueProcessor(AttributeHandlerStore):
	_valueLocks: DefaultDict[AttributeT, Lock]
	_valueTimes: DefaultDict[AttributeT, float]
	_values: Dict[AttributeT, Any]

	def __init__(self):
		super().__init__()
		self._valueLocks = DefaultDict(Lock)
		self._values = {}
		self._valueTimes = DefaultDict(time.time)

	def register(self, handler: AttributeReceiver):
		if not handler._isCatchAll:
			self._values[handler._attribute] = handler._defaultValueGetter(handler.__self__, attribute)
		return super().register(handler)

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
		handler = self._getHandler(attribute)
		value = handler(attribute, val)
		self.SetValue(attribute, value)


class RemoteProtocolHandler((AutoPropertyObject)):
	_dev: hwIo.IoBase
	driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlers: Dict[CommandT, CommandHandlerT]
	_attributeSenderStore: AttributeSenderStore
	_attributeValueProcessor: AttributeValueProcessor

	def __new__(cls, *args, **kwargs):
		self = super().__new__(cls, *args, **kwargs)
		self._attributeSenderStore = AttributeSenderStore()
		self._attributeValueProcessor = AttributeValueProcessor()
		commandHandlers = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_command")
		)
		self._commandHandlers = {v._command: getattr(self, k) for k, v in commandHandlers}
		senders = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_sendingAttribute")
		)
		for k, v in senders:
			self._attributeSenderStore.register(getattr(self, k))
		receivers = inspect.getmembers(
			cls,
			predicate=lambda o: inspect.isfunction(o) and hasattr(o, "_receivingAttribute")
		)
		for k, v in receivers:
			self._attributeValueProcessor.register(getattr(self, k))
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
			try:
				handler = self._attributeSenderStore._getHandler(attribute)
			except NotImplementedError:
				log.error(f"No attribute sender for attribute {attribute}")
				return
			handler(attribute)
		else:
			try:
				handler = self._attributeValueProcessor._getHandler(attribute)
			except NotImplementedError:
				log.error(f"No attribute receiver for attribute {attribute}")
				return
			handler(attribute, value)

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
		handler = self._attributeValueProcessor.get(attribute)
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
