import typing
import addonHandler
from enum import Enum, auto
from driverHandler import Driver
import api
from logHandler import log
import sys
import time
from extensionPoints import Decider
from ..objects import RemoteDesktopControl


if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS = 200


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipeBase
	decide_remoteDisconnect = Decider()
	_remoteSessionhasFocus: typing.Optional[bool] = None

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
		if isinstance(obj, RemoteDesktopControl) and obj.processID == self._dev.pipeProcessId:
			self._remoteSessionhasFocus = True
		else:
			self._remoteSessionhasFocus = None
		# Invalidate the property cache to ensure that hasFocus will be fetched again.
		# Normally, hasFocus should be cached since it is pretty expensive
		# and should never try to fetch the time since input from the remote driver
		# more than once per core cycle.
		# However, if we don't clear the cache here, the braille handler won't be enabled correctly
		# for the first focus outside the remote window.
		self.invalidateCache()

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

	hasFocus: bool

	def _get_hasFocus(self) -> bool:
		remoteProcessHasFocus = api.getFocusObject().processID == self._dev.pipeProcessId
		if not remoteProcessHasFocus:
			return remoteProcessHasFocus
		attribute = protocol.GenericAttribute.TIME_SINCE_INPUT
		if self._remoteSessionhasFocus is not None:
			return self._remoteSessionhasFocus
		log.debug("Requesting time since input from remote driver")
		self.requestRemoteAttribute(attribute)
		return False

	@protocol.attributeReceiver(protocol.GenericAttribute.TIME_SINCE_INPUT, defaultValue=False)
	def _incoming_timeSinceInput(self, payload: bytes) -> int:
		assert len(payload) == 4
		return int.from_bytes(payload, byteorder=sys.byteorder, signed=False)

	@_incoming_timeSinceInput.updateCallback
	def _post_timeSinceInput(self, attribute: protocol.AttributeT, value: int):
		assert attribute == protocol.GenericAttribute.TIME_SINCE_INPUT
		self._remoteSessionhasFocus = value <= MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS
		if self._remoteSessionhasFocus:
			self._handleRemoteSessionGainFocus()

	def _handleRemoteSessionGainFocus(self):
		return

	def _onReadError(self, error: int) -> bool:
		return self.decide_remoteDisconnect.decide(handler=self, pipeName=self.pipeName, error=error)
