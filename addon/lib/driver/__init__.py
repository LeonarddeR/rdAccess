from abc import abstractmethod
import driverHandler
from ..detection import bgScanRD, KEY_NAMED_PIPE_CLIENT, KEY_VIRTUAL_CHANNEL
from .. import protocol
from .. import wtsVirtualChannel
from .. import namedPipe
import inputCore
import keyboardHandler
import time
import sys
from typing import (
	Any,
	Iterable,
	Iterator,
	List,
	Optional,
	Union,
)
import bdDetect
from logHandler import log
from autoSettingsUtils.driverSetting import DriverSetting
from .settingsAccessor import SettingsAccessorBase


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

	def terminate(self):
		inputCore.decide_executeGesture.unregister(self._handleDecideExecuteGesture)
		try:
			super().terminate()
		finally:
			# Make sure the device gets closed.
			self._dev.close()

	def initSettings(self):
		"""Initializing settings not supported on this driver."""
		return

	def loadSettings(self, onlyChanged: bool = False):
		"""Loading settings not supported on this driver."""
		return

	def saveSettings(self):
		"""Saving settings not supported on this driver."""
		return

	def __init__(self, port="auto"):
		super().__init__()
		self._connected = False
		self._lastKeyboardGestureInputTime = time.time()
		self._gesturesToIntercept: List[List[str]] = []
		for portType, portId, port, portInfo in self._getTryPorts(port):
			try:
				if portType == KEY_VIRTUAL_CHANNEL:
					self._dev = wtsVirtualChannel.WTSVirtualChannel(
						port,
						onReceive=self._onReceive
					)
				elif portType == KEY_NAMED_PIPE_CLIENT:
					self._dev = namedPipe.NamedPipeClient(
						port,
						onReceive=self._onReceive
					)
			except EnvironmentError:
				log.debugWarning("", exc_info=True)
				continue
			if portType == KEY_VIRTUAL_CHANNEL:
				# Wait for RdPipe at the other end to send a XON
				for i in range(3):
					self._dev.waitForRead(self.timeout)
					if self._connected:
						break
				if self._connected:
					inputCore.decide_executeGesture.register(self._handleDecideExecuteGesture)
					break
			else:
				self._connected = True
				break
			self._dev.close()
		else:
			raise RuntimeError("No remote device found")

	def __getattribute__(self, name: str) -> Any:
		getter = super().__getattribute__
		if name.startswith("_") and not name.startswith("_get_"):
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

	def _handleDecideExecuteGesture(self, gesture):
		if isinstance(gesture, keyboardHandler.KeyboardInputGesture):
			self._lastKeyboardGestureInputTime = time.time()
			intercepting = next(
				(t for t in self._gesturesToIntercept if any(i for i in t if i in gesture.normalizedIdentifiers)),
				None
			)
			if intercepting is not None:
				self._gesturesToIntercept.remove(intercepting)
				log.debug(f"Intercepted gesture, execution canceled: {intercepting!r}")
				return False
		return True

	@abstractmethod
	def _handleRemoteDisconnect(self):
		raise NotImplementedError()

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

	@protocol.commandHandler(protocol.GenericCommand.INTERCEPT_GESTURE)
	def _interceptGesture(self, payload: bytes):
		intercepting = self._unpickle(payload=payload)
		log.debug(f"Instructed to intercept gesture {intercepting!r}")
		self._gesturesToIntercept.append(intercepting)

	@protocol.attributeSender(protocol.GenericAttribute.HAS_FOCUS)
	def _sendHasFocus(self) -> bytes:
		initialTime = time.time()
		result = self._safeWait(lambda: self._lastKeyboardGestureInputTime >= initialTime, timeout=self.timeout)
		return result.to_bytes(1, sys.byteorder)

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
		return self.getRemoteAttribute(protocol.GenericAttribute.SUPPORTED_SETTINGS, allowCache=True)

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, attribute: protocol.AttributeT, payLoad: bytes):
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	@protocol.attributeReceiver(b"available*s")
	def _incoming_availableSettingValues(self, attribute: protocol.AttributeT, payLoad: bytes):
		return self._unpickle(payLoad)
