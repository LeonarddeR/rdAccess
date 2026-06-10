# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023-2025 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0
from __future__ import annotations

import inspect
import pickle
import sys
import time
import weakref
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, IntEnum
from fnmatch import fnmatch
from functools import partial, update_wrapper, wraps
from typing import (
	Any,
	cast,
)

import addonHandler
import queueHandler
import versionInfo
from baseObject import AutoPropertyObject
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


CommandT = GenericCommand | SpeechCommand | BrailleCommand
AttributeT = GenericAttribute | SpeechAttribute | BrailleAttribute | bytes
# Handler functions are stored unbound; the first parameter is the RemoteProtocolHandler instance.
# It is typed as Any because typing it precisely would make subclass methods (whose self is the
# subclass) unassignable due to parameter contravariance.
CommandHandlerFuncT = Callable[[Any, bytes], None]
# Attribute handler functions vary in arity: catch-all handlers receive the concrete attribute as an
# extra argument and senders may take additional (keyword) arguments.
AttributeFetcherT = Callable[..., bytes]
AttributeReceiverFuncT = Callable[..., Any]
DefaultValueGetterT = Callable[[Any, AttributeT], Any]
AttributeValueUpdateCallbackT = Callable[[Any, AttributeT, Any], None]


class HandlerDecoratorBase[HandlerFuncT: Callable]:
	"""Decorator that marks a method as a protocol handler.

	Instances live on the class and hold the decorated function unbound;
	RemoteProtocolHandler.__new__ registers them on the per-instance handler stores,
	which pass the owning instance explicitly on dispatch.
	"""

	_func: HandlerFuncT

	def __init__(self, func: HandlerFuncT):
		self._func = func
		update_wrapper(self, func, assigned=("__module__", "__name__", "__qualname__", "__doc__"))

	def __set_name__(self, owner, name):
		log.debug(f"Decorated {name!r} on {owner!r} with {self!r}")

	def __call__(self, *args, **kwargs):
		# Concrete subclasses implement the actual dispatch; declaring it here lets the type
		# checker treat instances as callable (used by update_wrapper).
		raise NotImplementedError


class CommandHandler(HandlerDecoratorBase[CommandHandlerFuncT]):
	_command: CommandT

	def __init__(self, command: CommandT, func: CommandHandlerFuncT):
		super().__init__(func)
		self._command = command

	def __call__(self, protocolHandler: RemoteProtocolHandler, payload: bytes):
		log.debug(f"Calling {self!r} for command {self._command!r}")
		return self._func(protocolHandler, payload)


def commandHandler(command: CommandT):
	return partial(CommandHandler, command)


class AttributeHandler[AttributeHandlerFuncT: Callable](HandlerDecoratorBase[AttributeHandlerFuncT]):
	_attribute: AttributeT = b""

	@property
	def _isCatchAll(self) -> bool:
		return b"*" in self._attribute

	def __init__(self, attribute: AttributeT, func: AttributeHandlerFuncT):
		super().__init__(func)
		self._attribute = attribute

	def __call__(
		self,
		protocolHandler: RemoteProtocolHandler,
		attribute: AttributeT,
		*args,
		**kwargs,
	):
		log.debug(f"Calling {self!r} for attribute {attribute!r}")
		if self._isCatchAll:
			return self._func(protocolHandler, attribute, *args, **kwargs)
		return self._func(protocolHandler, *args, **kwargs)


class AttributeSender(AttributeHandler[AttributeFetcherT]):
	def __call__(
		self,
		protocolHandler: RemoteProtocolHandler,
		attribute: AttributeT,
		*args,
		**kwargs,
	):
		value = super().__call__(protocolHandler, attribute, *args, **kwargs)
		protocolHandler.setRemoteAttribute(attribute=attribute, value=value)


def attributeSender(attribute: AttributeT):
	return partial(AttributeSender, attribute)


class AttributeReceiver(AttributeHandler[AttributeReceiverFuncT]):
	_defaultValueGetter: DefaultValueGetterT
	_updateCallback: AttributeValueUpdateCallbackT | None

	def __init__(
		self,
		attribute: AttributeT,
		func: AttributeReceiverFuncT,
		defaultValueGetter: DefaultValueGetterT,
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


def _constantDefaultValueGetter(defaultValue: Any) -> DefaultValueGetterT:
	def _defaultValueGetter(_self: RemoteProtocolHandler, _attribute: AttributeT):
		return defaultValue

	return _defaultValueGetter


def attributeReceiver(
	attribute: AttributeT,
	defaultValue: Any = None,
	defaultValueGetter: DefaultValueGetterT | None = None,
	updateCallback: AttributeValueUpdateCallbackT | None = None,
):
	if defaultValue is not None and defaultValueGetter is not None:
		raise ValueError("Either defaultValue or defaultValueGetter is required, but not both")
	if defaultValueGetter is None:
		defaultValueGetter = _constantDefaultValueGetter(defaultValue)
	return partial(
		AttributeReceiver,
		attribute,
		defaultValueGetter=defaultValueGetter,
		updateCallback=updateCallback,
	)


class HandlerStoreBase:
	"""Base for the per-instance handler registries on a RemoteProtocolHandler.

	A store holds the class-level handler descriptors and a weak reference to its owning
	protocol handler, which is passed to the descriptors explicitly on dispatch.
	The reference is weak so a registry never keeps its owner alive.
	"""

	_owner: weakref.ref[RemoteProtocolHandler]

	def __init__(self, owner: RemoteProtocolHandler):
		self._owner = weakref.ref(owner)

	def _getOwner(self) -> RemoteProtocolHandler:
		owner = self._owner()
		if owner is None:
			raise NotImplementedError("The protocol handler that owns this store no longer exists")
		return owner


class CommandHandlerStore(HandlerStoreBase):
	_commandIndex: dict[CommandT, CommandHandler]

	def __init__(self, owner: RemoteProtocolHandler):
		super().__init__(owner)
		self._commandIndex = {}

	def register(self, handler: CommandHandler):
		self._commandIndex[handler._command] = handler

	def __call__(self, command: CommandT, payload: bytes):
		log.debug(f"Getting handler on {self!r} to process command {command!r}")
		handler = self._commandIndex.get(command)
		if handler is None:
			raise NotImplementedError(f"No command handler for command {command!r}")
		handler(self._getOwner(), payload)


class AttributeHandlerStore[AttributeHandlerT: AttributeHandler](HandlerStoreBase):
	_exactIndex: dict[AttributeT, AttributeHandlerT]
	_wildcardHandlers: list[AttributeHandlerT]

	def __init__(self, owner: RemoteProtocolHandler):
		super().__init__(owner)
		self._exactIndex = {}
		self._wildcardHandlers = []

	def register(self, handler: AttributeHandlerT):
		if handler._isCatchAll:
			self._wildcardHandlers.append(handler)
		else:
			self._exactIndex[handler._attribute] = handler

	def _getRawHandler(self, attribute: AttributeT) -> AttributeHandlerT:
		# Exact match takes priority over wildcard patterns (e.g. a specific attribute beats setting_*)
		handler = self._exactIndex.get(attribute)
		if handler is not None:
			return handler
		handler = next((h for h in self._wildcardHandlers if fnmatch(attribute, h._attribute)), None)
		if handler is None:
			raise NotImplementedError(f"No attribute sender for attribute {attribute}")
		return handler

	def isAttributeSupported(self, attribute: AttributeT):
		try:
			self._getRawHandler(attribute)
			return True
		except NotImplementedError:
			return False


class AttributeSenderStore(AttributeHandlerStore[AttributeSender]):
	def __call__(self, attribute: AttributeT, *args, **kwargs):
		log.debug(f"Getting handler on {self!r} to process attribute {attribute!r}")
		handler = self._getRawHandler(attribute)
		handler(self._getOwner(), attribute, *args, **kwargs)


class AttributeValueProcessor(AttributeHandlerStore[AttributeReceiver]):
	_valueTimes: defaultdict[AttributeT, float]
	_values: dict[AttributeT, Any]
	_pendingAttributeRequests: defaultdict[AttributeT, bool]

	def __init__(self, owner: RemoteProtocolHandler):
		super().__init__(owner)
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

	def _getDefaultAttributeValue(self, attribute: AttributeT) -> Any:
		handler = self._getRawHandler(attribute)
		log.debug(
			f"Getting default value for attribute {attribute!r} on {self!r} "
			f"using {handler._defaultValueGetter!r}",
		)
		return handler._defaultValueGetter(self._getOwner(), attribute)

	def _submitAttributeUpdateCallback(self, attribute: AttributeT, value: Any):
		handler = self._getRawHandler(attribute)
		if handler._updateCallback is not None:
			log.debug(f"Calling update callback {handler._updateCallback!r} for attribute {attribute!r}")
			owner = self._getOwner()
			owner._bgExecutor.submit(handler._updateCallback, owner, attribute, value)

	def getValue(self, attribute: AttributeT, fallBackToDefault: bool = False):
		if fallBackToDefault and attribute not in self._values:
			log.debug(f"No value for attribute {attribute!r} on {self!r}, falling back to default")
			self._values[attribute] = self._getDefaultAttributeValue(attribute)
		return self._values[attribute]

	def clearValue(self, attribute):
		self._values.pop(attribute, None)

	def setValue(self, attribute: AttributeT, value):
		self._values[attribute] = value
		self._valueTimes[attribute] = time.perf_counter()
		self._submitAttributeUpdateCallback(attribute, value)

	def __call__(self, attribute: AttributeT, rawValue: bytes):
		log.debug(f"Getting handler on {self!r} to process attribute {attribute!r}")
		handler = self._getRawHandler(attribute)
		value = handler(self._getOwner(), attribute, rawValue)
		log.debug(f"Handler on {self!r} returned value {value!r} for attribute {attribute!r}")
		self.setAttributeRequestPending(attribute, False)
		self.setValue(attribute, value)


class RemoteProtocolHandler[IoTypeT: IoBase](AutoPropertyObject):
	_dev: IoTypeT
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
		self._commandHandlerStore = CommandHandlerStore(self)
		self._attributeSenderStore = AttributeSenderStore(self)
		self._attributeValueProcessor = AttributeValueProcessor(self)
		handlers = inspect.getmembers(cls, predicate=lambda o: isinstance(o, HandlerDecoratorBase))
		for _name, handler in handlers:
			if isinstance(handler, CommandHandler):
				self._commandHandlerStore.register(handler)
			elif isinstance(handler, AttributeSender):
				self._attributeSenderStore.register(handler)
			elif isinstance(handler, AttributeReceiver):
				self._attributeValueProcessor.register(handler)
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
				f"actual length of payload {payload!r} is {actualLength}",
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
		attribute, rawValue = payload[1:].split(ATTRIBUTE_SEPARATOR, 1)
		log.debug(f"Handling attribute {attribute!r} on {self!r}, value {rawValue!r}")
		if not rawValue:
			log.debug(f"No value sent for attribute {attribute!r} on {self!r}, expecting a reply")
			self._attributeSenderStore(attribute)
		else:
			log.debug(
				f"Value of length {len(rawValue)} sent for attribute {attribute!r} "
				f"on {self!r}, direction incoming",
			)
			self._attributeValueProcessor(attribute, rawValue)

	@abstractmethod
	def _incoming_setting(self, attribute: AttributeT, payLoad: bytes):
		raise NotImplementedError

	def writeMessage(self, command: CommandT, payload: bytes = b""):
		data = bytes((
			self.driverType,
			command,
			*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
			*payload,
		))
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

	def _getRemoteAttributeValueWithFallback(self, attribute: AttributeT):
		try:
			return self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultAttributeValue(attribute)
			self.requestRemoteAttribute(attribute)
			return value

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
		return self._getRemoteAttributeValueWithFallback(GenericAttribute.NVDA_VERSION)

	@attributeSender(GenericAttribute.RD_ACCESS_VERSION)
	def _outgoing_rdAccessVersion(self) -> bytes:
		return addon.version.encode()

	@attributeReceiver(GenericAttribute.RD_ACCESS_VERSION, defaultValue="0.0")
	def _incoming_rdAccessVersion(self, payload: bytes) -> str:
		return payload.decode()

	def _get_rdAccessVersion(self) -> str:
		return self._getRemoteAttributeValueWithFallback(GenericAttribute.RD_ACCESS_VERSION)
