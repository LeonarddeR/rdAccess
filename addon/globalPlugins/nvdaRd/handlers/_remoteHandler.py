import typing
import addonHandler
import keyboardHandler
from enum import Enum, auto
from driverHandler import Driver

if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


class RemoteFocusState(Enum):
	NONE = auto()
	CLIENT_FOCUSED = auto()
	SESSION_PENDING = auto()
	SESSION_FOCUSED = auto()


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipeBase
	_focusLastSet: float
	_focusTestGesture = keyboardHandler.KeyboardInputGesture.fromName("alt+control+shift+f24")

	_driver: Driver
	_abstract__driver = True

	def _get__driver(self) -> Driver:
		raise NotImplementedError

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		super().__init__()
		try:
			IO = namedPipe.NamedPipeClient if isNamedPipeClient else namedPipe.NamedPipeServer
			self._dev = IO(pipeName=pipeName, onReceive=self._onReceive, onReadError=self._onReadError)
		except EnvironmentError:
			raise

	def _onReadError(self, error: int) -> bool:
		if error == 109:
			# Broken pipe error
			self.terminate()
			return True
		return False

	def terminate(self):
		# Make sure the device gets closed.
		self._dev._onReadError = None
		self._dev.close()

	def event_gainFocus(self, obj):
		return

	@protocol.attributeSender(protocol.GenericAttribute.SUPPORTED_SETTINGS)
	def _outgoing_supportedSettings(self) -> bytes:
		return self._pickle(self._driver.supportedSettings)

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
