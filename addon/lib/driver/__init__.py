# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import sys
import time
from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any

import bdDetect
import driverHandler
from autoSettingsUtils.driverSetting import DriverSetting
from baseObject import AutoPropertyObject
from logHandler import log
from utils.security import isRunningOnSecureDesktop, post_sessionLockStateChanged

from .. import inputTime, namedPipe, protocol, secureDesktop, wtsVirtualChannel
from ..detection import KEY_NAMED_PIPE_CLIENT, KEY_VIRTUAL_CHANNEL, bgScanRD
from .settingsAccessor import SettingsAccessorBase

ERROR_INVALID_HANDLE = 0x6
ERROR_PIPE_NOT_CONNECTED = 0xE9
MSG_XON = 0x11
MSG_XOFF = 0x13


class RemoteDriver(protocol.RemoteProtocolHandler, driverHandler.Driver):
	name = "remote"
	_settingsAccessor: SettingsAccessorBase | None = None
	_isVirtualChannel: bool
	_requiredAttributesOnInit: set[protocol.AttributeT] = {protocol.GenericAttribute.SUPPORTED_SETTINGS}

	@classmethod
	def check(cls):
		return any(cls._getAutoPorts())

	@classmethod
	def _getAutoPorts(cls, _usb=True, _bluetooth=True) -> Iterable[bdDetect.DeviceMatch]:
		for driver, match in bgScanRD(cls.driverType, [cls.name]):
			assert driver == cls.name
			yield match

	@classmethod
	def _getTryPorts(cls, port: str | bdDetect.DeviceMatch) -> Iterator[bdDetect.DeviceMatch]:
		if isinstance(port, bdDetect.DeviceMatch):
			yield port
		elif isinstance(port, str):
			assert port == "auto"
			yield from cls._getAutoPorts()

	_localSettings: list[DriverSetting] = []

	def initSettings(self):
		self._initSpecificSettings(self, self._localSettings)

	def loadSettings(self, onlyChanged: bool = False):
		self._loadSpecificSettings(self, self._localSettings, onlyChanged)

	def saveSettings(self):
		self._saveSpecificSettings(self, self._localSettings)

	def __init__(self, port="auto"):
		initialTime = time.perf_counter()
		super().__init__()
		self._connected = False
		for portType, _portId, port, _portInfo in self._getTryPorts(port):  # noqa: B020
			for attr in self._requiredAttributesOnInit:
				self._attributeValueProcessor.setAttributeRequestPending(attr)
			try:
				if portType == KEY_VIRTUAL_CHANNEL:
					self._isVirtualChannel = True
					self._dev = wtsVirtualChannel.WTSVirtualChannel(
						port,
						onReceive=self._onReceive,
						onReadError=self._onReadError,
					)
				elif portType == KEY_NAMED_PIPE_CLIENT:
					self._isVirtualChannel = False
					self._dev = namedPipe.NamedPipeClient(
						port,
						onReceive=self._onReceive,
						onReadError=self._onReadError,
					)
			except OSError:
				log.debugWarning("", exc_info=True)
				continue
			if portType == KEY_VIRTUAL_CHANNEL:
				# Wait for RdPipe at the other end to send a XON
				if not self._safeWait(lambda: self._connected, self.timeout * 3):
					continue
			else:
				self._connected = True
			handledAttributes = set()
			for attr in self._requiredAttributesOnInit:
				if self._waitForAttributeUpdate(attr, initialTime):
					handledAttributes.add(attr)
				else:
					log.debugWarning(f"Error getting {attr}")

			else:
				if handledAttributes == self._requiredAttributesOnInit:
					log.debug("Required attributes received")
					break

			self._dev.close()
		else:
			raise RuntimeError("No remote device found")

		if not isRunningOnSecureDesktop():
			post_sessionLockStateChanged.register(self._handlePossibleSessionDisconnect)
			secureDesktop.post_secureDesktopStateChange.register(self._handlePossibleSessionDisconnect)

	def terminate(self):
		if not isRunningOnSecureDesktop():
			secureDesktop.post_secureDesktopStateChange.unregister(self._handlePossibleSessionDisconnect)
			post_sessionLockStateChanged.unregister(self._handlePossibleSessionDisconnect)
		super().terminate()

	def __getattribute__(self, name: str) -> Any:
		getter = super().__getattribute__
		if (name.startswith("_") and not name.startswith("_get_")) or name in (
			n for n in dir(AutoPropertyObject) if not n.startswith("_")
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
		if error in (ERROR_PIPE_NOT_CONNECTED, ERROR_INVALID_HANDLE):
			self._handleRemoteDisconnect()
			return True
		return False

	@abstractmethod
	def _handleRemoteDisconnect(self):
		return

	def _onReceive(self, message: bytes):
		if self._isVirtualChannel and len(message) == 1:
			command = message[0]
			if command == MSG_XON:
				self._connected = True
				return
			elif command == MSG_XOFF:
				log.debugWarning("MSG_XOFF message received, connection closed")
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
		_attribute: protocol.AttributeT,
		settings: Iterable[DriverSetting],
	):
		log.debug(f"Initializing settings accessor for {len(settings)} settings")
		self._settingsAccessor = SettingsAccessorBase.createFromSettings(self, settings) if settings else None
		self._handleRemoteDriverChange()

	def _handleRemoteDriverChange(self):
		log.debug("Handling remote driver change")

	def _get_supportedSettings(self):
		settings = []
		settings.extend(self._localSettings)
		attribute = protocol.GenericAttribute.SUPPORTED_SETTINGS
		try:
			settings.extend(self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False))
		except KeyError:
			settings.extend(self.getRemoteAttribute(attribute))
		return settings

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, _attribute: protocol.AttributeT, payLoad: bytes):
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	@protocol.attributeReceiver(b"available*s")
	def _incoming_availableSettingValues(self, _attribute: protocol.AttributeT, payLoad: bytes):
		return self._unpickle(payLoad)

	@protocol.attributeSender(protocol.GenericAttribute.TIME_SINCE_INPUT)
	def _outgoing_timeSinceInput(self) -> bytes:
		return inputTime.getTimeSinceInput().to_bytes(4, sys.byteorder, signed=False)

	def _handlePossibleSessionDisconnect(self):
		if not self.check():
			self._handleRemoteDisconnect()
