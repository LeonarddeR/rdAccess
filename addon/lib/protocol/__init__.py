# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023-2025 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later
from __future__ import annotations

import inspect
import threading
import time
import weakref
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable
from fnmatch import fnmatch
from functools import partial, update_wrapper, wraps
from typing import Any

import addonHandler
import queueHandler
import versionInfo
from baseObject import AutoPropertyObject
from hwIo.base import IoBase
from logHandler import log

from . import legacy
from .braille import BrailleAttribute, BrailleCommand
from .legacy import ATTRIBUTE_SEPARATOR, GenericCommand
from .messages import (
	CHANNEL_NAMES,
	MSG_XOFF,
	MSG_XON,
	PROTOCOL_VERSION,
	DriverType,
	GenericAttribute,
	RdMessageType,
)
from .serializer import RdJSONSerializer
from .speech import SpeechAttribute, SpeechCommand

__all__ = [
	"ATTRIBUTE_SEPARATOR",
	"MSG_XOFF",
	"MSG_XON",
	"PROTOCOL_VERSION",
	"SETTING_ATTRIBUTE_PREFIX",
	"AttributeReceiver",
	"AttributeT",
	"BrailleAttribute",
	"BrailleCommand",
	"DriverType",
	"GenericAttribute",
	"GenericCommand",
	"PendingValueStore",
	"RdMessageType",
	"RemoteProtocolHandler",
	"SpeechAttribute",
	"SpeechCommand",
	"attributeReceiver",
	"attributeSender",
	"commandHandler",
	"legacy",
]

addon: addonHandler.Addon = addonHandler.getCodeAddon()
SETTING_ATTRIBUTE_PREFIX = "setting_"

AttributeT = str
# Handler functions are stored unbound; the first parameter is the RemoteProtocolHandler instance.
# It is typed as Any because typing it precisely would make subclass methods (whose self is the
# subclass) unassignable due to parameter contravariance.
CommandHandlerFuncT = Callable[..., None]
# Attribute handler functions vary in arity: catch-all handlers receive the concrete attribute as an
# extra argument and senders may take additional (keyword) arguments.
AttributeFetcherT = Callable[..., Any]
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
	_messageType: RdMessageType

	def __init__(self, messageType: RdMessageType, func: CommandHandlerFuncT):
		super().__init__(func)
		self._messageType = messageType

	def __call__(self, protocolHandler: RemoteProtocolHandler, **kwargs):
		log.debug(f"Calling {self!r} for message type {self._messageType!r}")
		return self._func(protocolHandler, **kwargs)


def commandHandler(messageType: RdMessageType):
	return partial(CommandHandler, messageType)


class AttributeHandler[AttributeHandlerFuncT: Callable](HandlerDecoratorBase[AttributeHandlerFuncT]):
	_attribute: AttributeT = ""

	@property
	def _isCatchAll(self) -> bool:
		return "*" in self._attribute

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


def _identityReceiver(_protocolHandler: Any, *args: Any) -> Any:
	return args[-1]


def _constantDefaultValueGetter(defaultValue: Any) -> DefaultValueGetterT:
	def _defaultValueGetter(_self: RemoteProtocolHandler, _attribute: AttributeT):
		return defaultValue

	return _defaultValueGetter


class AttributeReceiver(AttributeHandler[AttributeReceiverFuncT]):
	"""Receiver for a remote attribute value.

	Usable as a bare class attribute when the decoded value needs no transformation,
	or applied to a method (via the :func:`attributeReceiver` decorator) that
	normalizes the value before it is stored.
	"""

	_defaultValueGetter: DefaultValueGetterT
	_updateCallback: AttributeValueUpdateCallbackT | None

	def __init__(
		self,
		attribute: AttributeT,
		func: AttributeReceiverFuncT | None = None,
		defaultValue: Any = None,
		defaultValueGetter: DefaultValueGetterT | None = None,
		updateCallback: AttributeValueUpdateCallbackT | None = None,
	):
		if defaultValue is not None and defaultValueGetter is not None:
			raise ValueError("Either defaultValue or defaultValueGetter is required, but not both")
		super().__init__(attribute, func if func is not None else _identityReceiver)
		self._defaultValueGetter = defaultValueGetter or _constantDefaultValueGetter(defaultValue)
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
	return partial(
		AttributeReceiver,
		attribute,
		defaultValue=defaultValue,
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
	_commandIndex: dict[RdMessageType, CommandHandler]

	def __init__(self, owner: RemoteProtocolHandler):
		super().__init__(owner)
		self._commandIndex = {}

	def register(self, handler: CommandHandler):
		self._commandIndex[handler._messageType] = handler

	def __call__(self, messageType: RdMessageType, **kwargs):
		log.debug(f"Getting handler on {self!r} to process message type {messageType!r}")
		handler = self._commandIndex.get(messageType)
		if handler is None:
			raise NotImplementedError(f"No command handler for message type {messageType!r}")
		handler(self._getOwner(), **kwargs)


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

	def _invokeAttributeUpdateCallback(self, attribute: AttributeT, value: Any):
		handler = self._getRawHandler(attribute)
		if handler._updateCallback is not None:
			log.debug(f"Calling update callback {handler._updateCallback!r} for attribute {attribute!r}")
			handler._updateCallback(self._getOwner(), attribute, value)

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
		self._invokeAttributeUpdateCallback(attribute, value)

	def __call__(self, attribute: AttributeT, value: Any):
		log.debug(f"Getting handler on {self!r} to process attribute {attribute!r}")
		handler = self._getRawHandler(attribute)
		value = handler(self._getOwner(), attribute, value)
		log.debug(f"Handler on {self!r} returned value {value!r} for attribute {attribute!r}")
		self.setAttributeRequestPending(attribute, False)
		self.setValue(attribute, value)


_UNSET = object()


class PendingValueStore[KeyT, ValueT]:
	"""Thread-safe per-key store for values awaiting application on another thread.

	push stores the newest value for a key and returns True when the store was
	empty, i.e. when the caller should schedule a drain. A value stays visible to
	get until it has been applied, so readers observe the most recent value even
	while application is queued or in progress.
	"""

	_lock: threading.Lock
	_values: dict[KeyT, ValueT]

	def __init__(self):
		self._lock = threading.Lock()
		self._values = {}

	def push(self, key: KeyT, value: ValueT) -> bool:
		with self._lock:
			wasEmpty = not self._values
			self._values[key] = value
			return wasEmpty

	def get(self, key: KeyT, default: Any = None) -> Any:
		with self._lock:
			return self._values.get(key, default)

	def drain(self, apply: Callable[[KeyT, ValueT], None]):
		"""Apply every pending value, including ones pushed while draining.

		Application errors are logged and the value is skipped, so the drain
		always terminates with the store empty of applied (or failed) values.
		"""
		while True:
			with self._lock:
				if not self._values:
					return
				key, value = next(iter(self._values.items()))
			try:
				apply(key, value)
			except Exception:
				log.error(f"Error applying pending value for {key!r}", exc_info=True)
			finally:
				with self._lock:
					if self._values.get(key, _UNSET) == value:
						del self._values[key]


class RemoteProtocolHandler[IoTypeT: IoBase](AutoPropertyObject):
	_dev: IoTypeT
	driverType: DriverType
	_receiveBuffer: bytes
	_commandHandlerStore: CommandHandlerStore
	_attributeSenderStore: AttributeSenderStore
	_attributeValueProcessor: AttributeValueProcessor
	timeout: float = 1.0
	cachePropertiesByDefault = True
	# Stateless, so shared by all handlers.
	_serializer: RdJSONSerializer = RdJSONSerializer()
	_sendJson: bool = False

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
		self._receiveBuffer = b""
		self._sendLock = threading.Lock()

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

	def _onReceive(self, message: bytes):
		if self._receiveBuffer:
			message = self._receiveBuffer + message
			self._receiveBuffer = b""
		while message:
			firstByte = message[0]
			if firstByte == RdJSONSerializer.SEP[0]:
				# Tolerate stray separators between JSON lines.
				message = message[1:]
			elif firstByte == ord("{"):
				line, sep, message = message.partition(RdJSONSerializer.SEP)
				if not sep:
					self._receiveBuffer = line
					return
				try:
					self._handleJsonLine(line)
				except Exception:
					log.error(f"Error handling JSON line: {line!r}", exc_info=True)
			elif firstByte == self.driverType:
				message = self._parseLegacyFrame(message)
			else:
				raise RuntimeError(f"Unexpected payload: {message}")

	def _parseLegacyFrame(self, message: bytes) -> bytes:
		"""Dispatch one legacy frame from ``message``, buffering partial frames.

		Returns the remaining bytes after the frame, or ``b""`` when the frame is
		incomplete and has been stashed in the receive buffer.
		"""
		parsed = legacy.parseFrame(message)
		if parsed is None:
			log.debug(f"Incomplete legacy frame, buffering {len(message)} bytes")
			self._receiveBuffer = message
			return b""
		command, payload, rest = parsed
		try:
			self._handleLegacyFrame(command, payload)
		except Exception:
			log.error(f"Error handling legacy frame with command {command!r}", exc_info=True)
		return rest

	def _handleLegacyFrame(self, command: int, payload: bytes):
		messageType, kwargs = legacy.decodeCommandPayload(self.driverType, command, payload)
		self._handleMessage(messageType, kwargs)

	def _handleJsonLine(self, line: bytes):
		try:
			obj = self._serializer.deserialize(line)
		except ValueError:
			log.error(f"Error parsing incoming JSON line: {line!r}", exc_info=True)
			return
		if not isinstance(obj, dict):
			log.error(f"Incoming JSON line is not an object: {line!r}")
			return
		# A peer that speaks JSON is at least version 2, whether or not its
		# protocol_version message has arrived yet.
		self._notePeerProtocolVersion(PROTOCOL_VERSION)
		typeValue = obj.pop("type", None)
		try:
			messageType = RdMessageType(typeValue)
		except ValueError:
			log.warning(f"Unknown message type received: {typeValue!r}")
			return
		self._handleMessage(messageType, obj)

	def _handleMessage(self, messageType: RdMessageType, kwargs: dict[str, Any]):
		log.debug(f"Handling message of type {messageType!r} on {self!r}")
		self._commandHandlerStore(messageType, **kwargs)

	@commandHandler(RdMessageType.ATTRIBUTE_REQUEST)
	def _command_attributeRequest(self, attribute: AttributeT):
		self._attributeSenderStore(attribute)

	@commandHandler(RdMessageType.ATTRIBUTE_VALUE)
	def _command_attributeValue(self, attribute: AttributeT, value: Any):
		self._attributeValueProcessor(attribute, value)

	@commandHandler(RdMessageType.PING)
	def _command_ping(self):
		pass

	@commandHandler(RdMessageType.PROTOCOL_VERSION)
	def _command_protocolVersion(self, version: int, channel: str | None = None):
		if channel is not None and channel != CHANNEL_NAMES[self.driverType]:
			log.error(f"Protocol version message for unexpected channel {channel!r} on {self!r}")
			return
		self._notePeerProtocolVersion(version)

	def _notePeerProtocolVersion(self, version: int):
		if version > self._peerProtocolVersion:
			self._attributeValueProcessor.setValue(GenericAttribute.PROTOCOL_VERSION, version)

	@property
	def _peerProtocolVersion(self) -> int:
		return self._attributeValueProcessor.getValue(
			GenericAttribute.PROTOCOL_VERSION,
			fallBackToDefault=True,
		)

	@attributeSender(GenericAttribute.PROTOCOL_VERSION)
	def _outgoing_protocolVersion(self) -> int:
		return PROTOCOL_VERSION

	@attributeReceiver(GenericAttribute.PROTOCOL_VERSION, defaultValue=1)
	def _incoming_protocolVersion(self, value: int) -> int:
		return max(value, self._peerProtocolVersion)

	@_incoming_protocolVersion.updateCallback
	def _post_protocolVersion(self, _attribute: AttributeT, value: int):
		self._handlePeerProtocolVersionChange(value)

	def _handlePeerProtocolVersionChange(self, version: int):
		if version < PROTOCOL_VERSION or self._sendJson:
			return
		log.debug(f"Peer speaks protocol version {version}, switching to JSON Lines on {self!r}")
		self._sendJson = True
		self.sendMessage(
			RdMessageType.PROTOCOL_VERSION,
			version=PROTOCOL_VERSION,
			channel=CHANNEL_NAMES[self.driverType],
		)

	def pushProtocolVersion(self):
		"""Push our protocol version to the peer; call once when a connection is established."""
		self._attributeSenderStore(GenericAttribute.PROTOCOL_VERSION)

	@abstractmethod
	def _incoming_setting(self, attribute: AttributeT, value: Any):
		raise NotImplementedError

	def sendMessage(self, messageType: RdMessageType, **payload: Any):
		if self._sendJson:
			data = self._serializer.serialize(type=messageType, **payload)
		else:
			command, commandPayload = legacy.encodeCommandPayload(self.driverType, messageType, payload)
			data = legacy.packFrame(self.driverType, command, commandPayload)
		# IoBase.write reuses a single OVERLAPPED structure per device and byte-mode
		# channels give no message atomicity, so writes from concurrent threads
		# (main thread, IO thread, braille background thread) must be serialized.
		with self._sendLock:
			self._dev.write(data)

	def setRemoteAttribute(self, attribute: AttributeT, value: Any):
		log.debug(f"Setting remote attribute {attribute!r} to value {value!r}")
		self.sendMessage(RdMessageType.ATTRIBUTE_VALUE, attribute=attribute, value=value)

	def requestRemoteAttribute(self, attribute: AttributeT):
		if self._attributeValueProcessor.isAttributeRequestPending(attribute):
			log.debugWarning(f"Not requesting remote attribute {attribute!r},, request already pending")
			return
		log.debug(f"Requesting remote attribute {attribute!r}")
		self._attributeValueProcessor.setAttributeRequestPending(attribute)
		self.sendMessage(RdMessageType.ATTRIBUTE_REQUEST, attribute=attribute)

	def _safeWait(self, predicate: Callable[[], bool], timeout: float | None = None):
		ioThreadRef = getattr(self._dev, "_ioThreadRef", None)
		ioThread = ioThreadRef() if ioThreadRef is not None else None
		if ioThread is not None and threading.current_thread() is ioThread:
			raise RuntimeError("_safeWait may not be called on the device's IO thread")
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
	def _outgoing_nvdaVersion(self) -> str:
		return versionInfo.version_detailed

	_incoming_nvdaVersion = AttributeReceiver(GenericAttribute.NVDA_VERSION, defaultValue="0.0.0")

	def _get_nvdaVersion(self) -> str:
		return self._getRemoteAttributeValueWithFallback(GenericAttribute.NVDA_VERSION)

	@attributeSender(GenericAttribute.RD_ACCESS_VERSION)
	def _outgoing_rdAccessVersion(self) -> str:
		return addon.version

	_incoming_rdAccessVersion = AttributeReceiver(GenericAttribute.RD_ACCESS_VERSION, defaultValue="0.0")

	def _get_rdAccessVersion(self) -> str:
		return self._getRemoteAttributeValueWithFallback(GenericAttribute.RD_ACCESS_VERSION)
