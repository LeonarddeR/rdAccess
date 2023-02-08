import typing
import addonHandler
from enum import Enum, auto
from driverHandler import Driver
import api
from logHandler import log
import sys
import time
from extensionPoints import Decider
from functools import partial

if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS = 200


class RemoteFocusState(Enum):
	NONE = auto()
	CLIENT_FOCUSED = auto()
	SESSION_PENDING = auto()
	SESSION_FOCUSED = auto()


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipeBase
	_focusLastSet: float
	decide_remoteDisconnect = Decider()

	_driver: Driver
	_abstract__driver = True

	def _get__driver(self) -> Driver:
		raise NotImplementedError

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		super().__init__()
		self.pipeName = pipeName
		try:
			IO = namedPipe.NamedPipeClient if isNamedPipeClient else namedPipe.NamedPipeServer
			self._dev = IO(
				pipeName=pipeName,
				onReceive=self._onReceive,
				onReadError=self._onReadError
			)
		except EnvironmentError:
			raise

	def event_gainFocus(self, obj):
		self._focusLastSet = time.time()

	@protocol.attributeSender(protocol.GenericAttribute.SUPPORTED_SETTINGS)
	def _outgoing_supportedSettings(self, settings=None) -> bytes:
		if settings is None:
			settings = self._driver.supportedSettings
		return self._pickle(settings)

	@protocol.attributeSender(b"available*s")
	def _outgoing_availableSettingValues(self, attribute: protocol.AttributeT) -> bytes:
		name = attribute.decode("ASCII")
		return self._pickle(getattr(self._driver, name))

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, attribute: protocol.AttributeT, payLoad: bytes):
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	@_incoming_setting.updateCallback
	def _setIncomingSettingOnDriver(self, attribute: protocol.AttributeT, value: typing.Any):
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX):].decode("ASCII")
		setattr(self._driver, name, value)

	@protocol.attributeSender(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _outgoing_setting(self, attribute: protocol.AttributeT):
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX):].decode("ASCII")
		return self._pickle(getattr(self._driver, name))

	hasFocus: RemoteFocusState

	def _get_hasFocus(self) -> RemoteFocusState:
		remoteProcessHasFocus = api.getFocusObject().processID == self._dev.pipeProcessId
		if not remoteProcessHasFocus:
			return RemoteFocusState.NONE
		attribute = protocol.GenericAttribute.TIME_SINCE_INPUT
		if self._attributeValueProcessor.hasNewValueSince(attribute, self._focusLastSet):
			newValue = self._attributeValueProcessor.getValue(attribute)
			return (
				RemoteFocusState.SESSION_FOCUSED
				if newValue < MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS
				else RemoteFocusState.CLIENT_FOCUSED
			)
		log.debug("Requesting time since input from remote driver")
		self.requestRemoteAttribute(protocol.GenericAttribute.TIME_SINCE_INPUT)
		return RemoteFocusState.SESSION_PENDING

	@protocol.attributeReceiver(protocol.GenericAttribute.TIME_SINCE_INPUT, defaultValue=False)
	def _incoming_timeSinceInput(self, payload: bytes) -> int:
		assert len(payload) == 4
		return int.from_bytes(payload, byteorder=sys.byteorder, signed=False)

	def _onReadError(self, error: int) -> bool:
		return self.decide_remoteDisconnect.decide(handler=self, pipeName=self.pipeName, error=error)
