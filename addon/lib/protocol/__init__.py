# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023-2025 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import inspect
import pickle
import sys
import time
import types
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, IntEnum
from fnmatch import fnmatch
from functools import partial, update_wrapper, wraps
from typing import (
	Any,
	Generic,
	TypeVar,
	cast,
)

import addonHandler
import queueHandler
import versionInfo
from baseObject import AutoPropertyObject
from extensionPoints import HandlerRegistrar
from hwIo.base import IoBase
from logHandler import log

from .braille import BrailleAttribute, BrailleCommand
from .speech import SpeechAttribute, SpeechCommand

addon: addonHandler.Addon = addonHandler.getCodeAddon()
ATTRIBUTE_SEPARATOR = b"`"
SETTING_ATTRIBUTE_PREFIX = b"setting_"


class DriverType(IntEnum):
	SPEECH = ord(b"S")
	BRAILLE = ord(b"B")


class GenericCommand(IntEnum):
	ATTRIBUTE = ord(b"@")


class GenericAttribute(bytes, Enum):
	TIME_SINCE_INPUT = b"timeSinceInput"
	SUPPORTED_SETTINGS = b"supportedSettings"
	NVDA_VERSION = b"nvdaVersion"
	RD_ACCESS_VERSION = b"rdAccessVersion"


RemoteProtocolHandlerT = TypeVar("RemoteProtocolHandlerT", bound="RemoteProtocolHandler")
HandlerFuncT = TypeVar("HandlerFuncT", bound=Callable)
AttributeValueT = TypeVar("AttributeValueT")
CommandT = GenericCommand | SpeechCommand | BrailleCommand
CommandHandlerUnboundT = Callable[[RemoteProtocolHandlerT, bytes], None]
CommandHandlerT = Callable[[bytes], None]
AttributeT = GenericAttribute | SpeechAttribute | BrailleAttribute | bytes
attributeFetcherT = Callable[..., bytes]
attributeSenderT = Callable[..., None]
AttributeReceiverT = Callable[[bytes], AttributeValueT]
AttributeReceiverUnboundT = Callable[[RemoteProtocolHandlerT, bytes], AttributeValueT]
WildCardAttributeReceiverT = Callable[[AttributeT, bytes], AttributeValueT]
WildCardAttributeReceiverUnboundT = Callable[[RemoteProtocolHandlerT, AttributeT, bytes], AttributeValueT]
AttributeHandlerT = TypeVar(
	"AttributeHandlerT",
	attributeFetcherT,
	AttributeReceiverUnboundT,
	WildCardAttributeReceiverUnboundT,
)
DefaultValueGetterT = Callable[[RemoteProtocolHandlerT, AttributeT], AttributeValueT]
AttributeValueUpdateCallbackT = Callable[[RemoteProtocolHandlerT, AttributeT, AttributeValueT], None]


class HandlerDecoratorBase(Generic[HandlerFuncT]):
	_func: HandlerFuncT

	def __init__(self, func: HandlerFuncT):
		self._func = func
		update_wrapper(self, func, assigned=("__module__", "__name__", "__qualname__", "__doc__"))

	def __set_name__(self, owner, name):
		log.debug(f"Decorated {name!r} on {owner!r} with {self!r}")

	def __get__(self, obj, objtype=None):
		if obj is None:
			return self
		return types.MethodType(self, obj)


class CommandHandler(HandlerDecoratorBase[CommandHandlerT]):
	_command: CommandT

	def __init__(self, command: CommandT, func: CommandHandlerT):
		super().__init__(func)
		self._command = command

	def __call__(self, protocolHandler: "RemoteProtocolHandler", payload: bytes):
		log.debug(f"Calling {self!r} for command {self._command!r}")
		return self._func(protocolHandler, payload)


def commandHandler(command: CommandT):
	return partial(CommandHandler, command)


class AttributeHandler(HandlerDecoratorBase, Generic[AttributeHandlerT]):
	_attribute: AttributeT = b""

	@property
	def _isCatchAll(self) -> bool:
		return b"*" in self._attribute

	def __init__(self, attribute: AttributeT, func: AttributeHandlerT):
		super().__init__(func)
		self._attribute = attribute

	def __call__(
		self,
		protocolHandler: "RemoteProtocolHandler",
		attribute: AttributeT,
		*args,
		**kwargs,
	):
		log.debug(f"Calling {self!r} for attribute {attribute!r}")
		if self._isCatchAll:
			return self._func(protocolHandler, attribute, *args, **kwargs)
		return self._func(protocolHandler, *args, **kwargs)


class AttributeSender(AttributeHandler[attributeFetcherT]):
	def __call__(
		self,
		protocolHandler: RemoteProtocolHandlerT,
		attribute: AttributeT,
		*args,
		**kwargs,
	):
		value = super().__call__(protocolHandler, attribute, *args, **kwargs)
		protocolHandler.setRemoteAttribute(attribute=attribute, value=value)


def attributeSender(attribute: AttributeT):
	return partial(AttributeSender, attribute)


class AttributeReceiver(AttributeHandler[AttributeReceiverUnboundT | WildCardAttributeReceiverUnboundT]):
	_defaultValueGetter: DefaultValueGetterT | None
	_updateCallback: AttributeValueUpdateCallbackT | None

	def __init__(
		self,
		attribute: AttributeT,
		func: AttributeReceiverUnboundT | WildCardAttributeReceiverUnboundT,
		defaultValueGetter: DefaultValueGetterT | None,
		updateCallback: AttributeValueUpdateCallbackT | None,
	):
		super().__init__(attribute, func)
		self._defaultValueGetter = defaultValueGetter
		self._updateCallback = updateCallback

	def defaultValueGetter(self, func: DefaultValueGetterT):
		self._defaultValueGetter = func
		return func

	def updateCallback(self, func: AttributeValueUpdateCallbackT):
		self._updateCallback = func
		return func


def attributeReceiver(
	attribute: AttributeT,
	defaultValue: Any = None,
	defaultValueGetter: DefaultValueGetterT | None = None,
	updateCallback: AttributeValueUpdateCallbackT | None = None,
):
	if defaultValue is not None and defaultValueGetter is not None:
		raise ValueError("Either defaultValue or defaultValueGetter is required, but not both")
	if defaultValueGetter is None:

		def _defaultValueGetter(_self: "RemoteProtocolHandler", _attribute: AttributeT):
			return defaultValue

		defaultValueGetter = _defaultValueGetter
	return partial(
		AttributeReceiver,
		attribute,
		defaultValueGetter=defaultValueGetter,
		updateCallback=updateCallback,
	)


class CommandHandlerStore(HandlerRegistrar):
	def _getHandler(self, command: CommandT) -> CommandHandlerT:
		handler = next((v for v in self.handlers if command == v._command), None)
		if handler is None:
			raise NotImplementedError(f"No command handler for command {command!r}")
		return handler

	def __call__(self, command: CommandT, payload: bytes):
		log.debug(f"Getting handler on {self!r} to process command {command!r}")
		handler = self._getHandler(command)
		handler(payload)


class AttributeHandlerStore(HandlerRegistrar, Generic[AttributeHandlerT]):
	def _getRawHandler(self, attribute: AttributeT) -> AttributeHandlerT:
		handler = next((v for v in self.handlers if fnmatch(attribute, v._attribute)), None)
		if handler is None:
			raise NotImplementedError(f"No attribute sender for attribute {attribute}")
		return handler

	def _getHandler(self, attribute: AttributeT) -> AttributeHandlerT:
		return partial(self._getRawHandler(attribute), attribute)

	def isAttributeSupported(self, attribute: AttributeT):
		try:
			return self._getHandler(attribute) is not None
		except NotImplementedError:
			return False


class AttributeSenderStore(AttributeHandlerStore[attributeSenderT]):
	def __call__(self, attribute: AttributeT, *args, **kwargs):
		log.debug(f"Getting handler on {self!r} to process attribute {attribute!r}")
		handler = self._getHandler(attribute)
		handler(*args, **kwargs)


class AttributeValueProcessor(AttributeHandlerStore[AttributeReceiverT]):
	_valueTimes: defaultdict[AttributeT, float]
	_values: dict[AttributeT, Any]
	_pendingAttributeRequests: defaultdict[AttributeT, bool]

	def __init__(self):
		super().__init__()
		self._values = {}
		self._valueTimes = defaultdict(float)
		self._pendingAttributeRequests = defaultdict(bool)

	def clearCache(self):
		self._values.clear()
		self._valueTimes.clear()
		self._pendingAttributeRequests.clear()

	def setAttributeRequestPending(self, attribute: AttributeT, state: bool = True):
		log.debug(f"Request pending for attribute {attribute!r} set to {state!r}")
		self._pendingAttributeRequests[attribute] = state

	def isAttributeRequestPending(self, attribute: AttributeT) -> bool:
		return self._pendingAttributeRequests[attribute] is True

	def hasNewValueSince(self, attribute: AttributeT, t: float) -> bool:
		return t <= self._valueTimes[attribute]

	def _getDefaultValue(self, attribute: AttributeT) -> AttributeValueT:
		handler = self._getRawHandler(attribute)
		log.debug(
			f"Getting default value for attribute {attribute!r} on {self!r} "
			f"using {handler._defaultValueGetter!r}"
		)
		getter = handler._defaultValueGetter.__get__(handler.__self__)
		return getter(attribute)

	def _invokeUpdateCallback(self, attribute: AttributeT, value: AttributeValueT):
		handler = self._getRawHandler(attribute)
		if handler._updateCallback is not None:
			callback = handler._updateCallback.__get__(handler.__self__)
			log.debug(f"Calling update callback {callback!r} for attribute {attribute!r}")
			handler.__self__._bgExecutor.submit(callback, attribute, value)

	def getValue(self, attribute: AttributeT, fallBackToDefault: bool = False):
		if fallBackToDefault and attribute not in self._values:
			log.debug(f"No value for attribute {attribute!r} on {self!r}, falling back to default")
			self._values[attribute] = self._getDefaultValue(attribute)
		return self._values[attribute]

	def clearValue(self, attribute):
		self._values.pop(attribute, None)

	def setValue(self, attribute: AttributeT, value):
		self._values[attribute] = value
		self._valueTimes[attribute] = time.perf_counter()
		self._invokeUpdateCallback(attribute, value)

	def __call__(self, attribute: AttributeT, rawValue: bytes):
		log.debug(f"Getting handler on {self!r} to process attribute {attribute!r}")
		handler = self._getHandler(attribute)
		value = handler(rawValue)
		log.debug(f"Handler on {self!r} returned value {value!r} for attribute {attribute!r}")
		self.setAttributeRequestPending(attribute, False)
		self.setValue(attribute, value)


class RemoteProtocolHandler(AutoPropertyObject):
	_dev: IoBase
	driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlerStore: CommandHandlerStore
	_attributeSenderStore: AttributeSenderStore
	_attributeValueProcessor: AttributeValueProcessor
	timeout: float = 1.0
	cachePropertiesByDefault = True
	_bgExecutor: ThreadPoolExecutor

	def __new__(cls, *args, **kwargs):
		self = super().__new__(cls, *args, **kwargs)
		self._commandHandlerStore = CommandHandlerStore()
		self._attributeSenderStore = AttributeSenderStore()
		self._attributeValueProcessor = AttributeValueProcessor()
		handlers = inspect.getmembers(cls, predicate=lambda o: isinstance(o, HandlerDecoratorBase))
		for k, v in handlers:
			if isinstance(v, CommandHandler):
				self._commandHandlerStore.register(getattr(self, k))
			elif isinstance(v, AttributeSender):
				self._attributeSenderStore.register(getattr(self, k))
			elif isinstance(v, AttributeReceiver):
				self._attributeValueProcessor.register(getattr(self, k))
		return self

	def terminateIo(self):
		# Make sure the device gets closed.
		self._dev.close()

	def __init__(self):
		super().__init__()
		self._bgExecutor = ThreadPoolExecutor(4, thread_name_prefix=self.__class__.__name__)
		self._receiveBuffer = b""

	def terminate(self):
		try:
			superTerminate = getattr(super(), "terminate", None)
			if superTerminate:
				superTerminate()
				# We must sleep before closing the  connection as not doing this
				# can leave a remote handler in a bad state where it can not be re-initialized.
				time.sleep(self.timeout / 10)
		finally:
			self.terminateIo()
			self._attributeValueProcessor.clearCache()
			self._bgExecutor.shutdown()

	def _onReceive(self, message: bytes):
		if self._receiveBuffer:
			message = self._receiveBuffer + message
			self._receiveBuffer = b""
		if not message[0] == self.driverType:
			raise RuntimeError(f"Unexpected payload: {message}")
		command = cast(CommandT, message[1])
		expectedLength = int.from_bytes(message[2:4], sys.byteorder)
		payload = message[4:]
		actualLength = len(payload)
		remainder: bytes | None = None
		if expectedLength != actualLength:
			log.debug(
				f"Expected payload of length {expectedLength}, "
				f"actual length of payload {payload!r} is {actualLength}"
			)
			if expectedLength > actualLength:
				self._receiveBuffer = message
				return
			else:
				remainder = payload[expectedLength:]
				payload = payload[:expectedLength]

		try:
			self._bgExecutor.submit(self._commandHandlerStore, command, payload)
		finally:
			if remainder:
				self._onReceive(remainder)

	@commandHandler(GenericCommand.ATTRIBUTE)
	def _command_attribute(self, payload: bytes):
		attribute, value = payload[1:].split(b"`", 1)
		log.debug(f"Handling attribute {attribute!r} on {self!r}, value {value!r}")
		if not value:
			log.debug(f"No value sent for attribute {attribute!r} on {self!r}, direction outgoing")
			self._attributeSenderStore(attribute)
		else:
			log.debug(
				f"Value of length {len(value)} sent for attribute {attribute!r} "
				f"on {self!r}, direction incoming"
			)
			self._attributeValueProcessor(attribute, value)

	@abstractmethod
	def _incoming_setting(self, attribute: AttributeT, payLoad: bytes):
		raise NotImplementedError

	def writeMessage(self, command: CommandT, payload: bytes = b""):
		data = bytes(
			(
				self.driverType,
				command,
				*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
				*payload,
			)
		)
		self._dev.write(data)

	def setRemoteAttribute(self, attribute: AttributeT, value: bytes):
		log.debug(f"Setting remote attribute {attribute!r} to raw value {value!r}")
		return self.writeMessage(
			GenericCommand.ATTRIBUTE,
			ATTRIBUTE_SEPARATOR + attribute + ATTRIBUTE_SEPARATOR + value,
		)

	def requestRemoteAttribute(self, attribute: AttributeT):
		if self._attributeValueProcessor.isAttributeRequestPending(attribute):
			log.debugWarning(f"Not requesting remote attribute {attribute!r},, request already pending")
			return
		log.debug(f"Requesting remote attribute {attribute!r}")
		self._attributeValueProcessor.setAttributeRequestPending(attribute)
		self.writeMessage(
			GenericCommand.ATTRIBUTE,
			ATTRIBUTE_SEPARATOR + attribute + ATTRIBUTE_SEPARATOR,
		)

	def _safeWait(self, predicate: Callable[[], bool], timeout: float | None = None):
		if timeout is None:
			timeout = self.timeout
		log.debug(f"Waiting for {predicate!r} during {timeout} seconds")
		while timeout > 0.0:
			if predicate():
				log.debug(f"Waiting for {predicate!r} succeeded, {timeout} seconds remaining")
				return True
			curTime = time.perf_counter()
			res: bool = self._dev.waitForRead(timeout=timeout)
			if res is False:
				log.debug(f"Waiting for read for {predicate!r} failed. Predicate may still be True")
				break
			timeout -= time.perf_counter() - curTime
		return predicate()

	def getRemoteAttribute(
		self,
		attribute: AttributeT,
		timeout: float | None = None,
	):
		initialTime = time.perf_counter()
		self.requestRemoteAttribute(attribute=attribute)
		if self._waitForAttributeUpdate(attribute, initialTime, timeout):
			newValue = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
			log.debug(f"Received new value {newValue!r} for remote attribute {attribute!r}")
			return newValue
		raise TimeoutError(f"Wait for remote attribute {attribute} timed out")

	def _waitForAttributeUpdate(
		self,
		attribute: AttributeT,
		initialTime: float | None = None,
		timeout: float | None = None,
	):
		if initialTime is None:
			initialTime = 0.0
		log.debug(f"Waiting for attribute {attribute!r}")
		result = self._safeWait(
			lambda: self._attributeValueProcessor.hasNewValueSince(attribute, initialTime),
			timeout=timeout,
		)
		if result:
			log.debug(f"Waiting for attribute {attribute} succeeded")
		else:
			log.debug(f"Waiting for attribute {attribute} failed")
		return result

	def _pickle(self, obj: Any):
		return pickle.dumps(obj, protocol=4)

	def _unpickle(self, payload: bytes) -> Any:
		res = pickle.loads(payload)
		if isinstance(res, AutoPropertyObject):
			res.invalidateCache()
		return res

	def _queueFunctionOnMainThread(self, func, *args, **kwargs):
		@wraps(func)
		def wrapper(*args, **kwargs):
			log.debug(f"Executing {func!r}({args!r}, {kwargs!r}) on main thread")
			try:
				func(*args, **kwargs)
			except Exception:
				log.debug(
					f"Error executing {func!r}({args!r}, {kwargs!r}) on main thread",
					exc_info=True,
				)

		queueHandler.queueFunction(queueHandler.eventQueue, wrapper, *args, **kwargs)

	@abstractmethod
	def _onReadError(self, error: int) -> bool:
		return False

	@attributeSender(GenericAttribute.NVDA_VERSION)
	def _outgoing_nvdaVersion(self) -> bytes:
		return versionInfo.version_detailed.encode()

	@attributeReceiver(GenericAttribute.NVDA_VERSION, defaultValue="0.0.0")
	def _incoming_nvdaVersion(self, payload: bytes) -> str:
		return payload.decode()

	def _get_nvdaVersion(self) -> str:
		attribute = GenericAttribute.NVDA_VERSION
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value

	@attributeSender(GenericAttribute.RD_ACCESS_VERSION)
	def _outgoing_rdAccessVersion(self) -> bytes:
		return addon.version.encode()

	@attributeReceiver(GenericAttribute.RD_ACCESS_VERSION, defaultValue="0.0")
	def _incoming_rdAccessVersion(self, payload: bytes) -> str:
		return payload.decode()

	def _get_rdAccessVersion(self) -> str:
		attribute = GenericAttribute.RD_ACCESS_VERSION
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value
