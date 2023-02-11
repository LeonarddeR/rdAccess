from abc import abstractmethod
import driverHandler
from ..detection import bgScanRD, KEY_NAMED_PIPE_CLIENT, KEY_VIRTUAL_CHANNEL
from .. import protocol, inputTime
from .. import wtsVirtualChannel
from .. import namedPipe
from typing import (
	Any,
	Iterable,
	Iterator,
	Optional,
	Union,
)
import bdDetect
from logHandler import log
from autoSettingsUtils.driverSetting import DriverSetting
from .settingsAccessor import SettingsAccessorBase
import sys
from baseObject import AutoPropertyObject
from hwIo.ioThread import IoThread

ERROR_PIPE_NOT_CONNECTED = 0xe9
MSG_XON = 0x11
MSG_XOFF = 0x13


class RemoteDriver(protocol.RemoteProtocolHandler, driverHandler.Driver):
	name = "remote"
	_settingsAccessor: Optional[SettingsAccessorBase] = None

	@classmethod
	def check(cls):
		return any(cls._getAutoPorts())

	@classmethod
	def _getAutoPorts(cls, usb=True, bluetooth=True) -> Iterable[bdDetect.DeviceMatch]:
		for driver, match in bgScanRD(cls.driverType, [cls.name]):
			assert driver == cls.name
			yield match

	@classmethod
	def _getTryPorts(cls, port: Union[str, bdDetect.DeviceMatch]) -> Iterator[bdDetect.DeviceMatch]:
		if isinstance(port, bdDetect.DeviceMatch):
			yield port
		elif isinstance(port, str):
			assert port == "auto"
			for match in cls._getAutoPorts():
				yield match

	def initSettings(self):
		super(driverHandler.Driver, self).initSettings()

	def loadSettings(self, onlyChanged: bool = False):
		"""Loading settings not supported on this driver."""
		return

	def saveSettings(self):
		"""Saving settings not supported on this driver."""
		return

	def __init__(self, port="auto", ioThread: Optional[IoThread] = None):
		super().__init__()
		self._connected = False
		for portType, portId, port, portInfo in self._getTryPorts(port):
			try:
				if portType == KEY_VIRTUAL_CHANNEL:
					self._dev = wtsVirtualChannel.WTSVirtualChannel(
						port,
						onReceive=self._onReceive,
						onReadError=self._onReadError,
						ioThread=ioThread
					)
				elif portType == KEY_NAMED_PIPE_CLIENT:
					self._dev = namedPipe.NamedPipeClient(
						port,
						onReceive=self._onReceive,
						ioThread=ioThread
					)
			except EnvironmentError:
				log.debugWarning("", exc_info=True)
				continue
			if portType == KEY_VIRTUAL_CHANNEL:
				# Wait for RdPipe at the other end to send a XON
				if self._safeWait(lambda: self._connected, self.timeout * 3):
					break
			else:
				self._connected = True
				break
			self._dev.close()
		else:
			raise RuntimeError("No remote device found")

	def __getattribute__(self, name: str) -> Any:
		getter = super().__getattribute__
		if (
			(name.startswith("_") and not name.startswith("_get_"))
			or name in (n for n in dir(AutoPropertyObject) if not n.startswith("_"))
		):
			return getter(name)
		accessor = getter("_settingsAccessor")
		if accessor and name in dir(accessor):
			return getattr(accessor, name)
		return getter(name)

	def __setattr__(self, name: str, value: Any) -> None:
		getter = super().__getattribute__
		accessor = getter("_settingsAccessor")
		if accessor and getter("isSupported")(name):
			setattr(accessor, name, value)
		super().__setattr__(name, value)

	def _onReadError(self, error: int) -> bool:
		if error == ERROR_PIPE_NOT_CONNECTED:
			self._handleRemoteDisconnect()
			return True
		return False

	@abstractmethod
	def _handleRemoteDisconnect(self):
		self.terminate()

	def _onReceive(self, message: bytes):
		if isinstance(self._dev, wtsVirtualChannel.WTSVirtualChannel) and len(message) == 1:
			command = message[0]
			if command == MSG_XON:
				self._connected = True
				return
			elif command == MSG_XOFF:
				self._handleRemoteDisconnect()
				return
		super()._onReceive(message)

	@protocol.attributeReceiver(protocol.GenericAttribute.SUPPORTED_SETTINGS, defaultValue=[])
	def _incomingSupportedSettings(self, payLoad: bytes):
		assert len(payLoad) > 0
		settings = self._unpickle(payLoad)
		for s in settings:
			s.useConfig = False
		return settings

	@_incomingSupportedSettings.updateCallback
	def _updateCallback_supportedSettings(
			self,
			attribute: protocol.AttributeT,
			settings: Iterable[DriverSetting]
	):
		self._settingsAccessor = SettingsAccessorBase.createFromSettings(self, settings) if settings else None

	def _get_supportedSettings(self):
		attribute = protocol.GenericAttribute.SUPPORTED_SETTINGS
		try:
			return self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			return self.getRemoteAttribute(attribute)

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, attribute: protocol.AttributeT, payLoad: bytes):
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	@protocol.attributeReceiver(b"available*s")
	def _incoming_availableSettingValues(self, attribute: protocol.AttributeT, payLoad: bytes):
		return self._unpickle(payLoad)

	@protocol.attributeSender(protocol.GenericAttribute.TIME_SINCE_INPUT)
	def _outgoing_timeSinceInput(self) -> bytes:
		return inputTime.getTimeSinceInput().to_bytes(4, sys.byteorder, signed=False)
