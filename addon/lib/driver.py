from abc import abstractmethod
import driverHandler
from .detection import bgScanRD, KEY_NAMED_PIPE_CLIENT, KEY_VIRTUAL_CHANNEL
from . import protocol
from . import wtsVirtualChannel
from . import namedPipe
import inputCore
import keyboardHandler
import time
import sys
from typing import (
	Iterable,
	Iterator,
	List,
	Union,
)
import bdDetect
from logHandler import log


MSG_XON = 0x11
MSG_XOFF = 0x13


class RemoteDriver(protocol.RemoteProtocolHandler, driverHandler.Driver):
	name = "remote"
	timeout = 0.5

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
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		try:
			super().terminate()
		finally:
			# Make sure the device gets closed.
			self._dev.close()

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
					inputCore.decide_executeGesture.register(self._handleExecuteGesture)
					break
			else:
				self._connected = True
				break
			self._dev.close()
		else:
			raise RuntimeError("No remote device found")

		for handler in self._attributeSenders.values():
			handler()

	def _handleExecuteGesture(self, gesture):
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
