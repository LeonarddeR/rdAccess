from abc import abstractmethod
from driverHandler import Driver
from .sessionTrackingEx import WTSIsRemoteSession
from . import protocol
from . import wtsVirtualChannel


class RemoteDriver(protocol.RemoteProtocolHandler, Driver):

	def __init__(self, driverType: protocol.DriverType):
		protocol.RemoteProtocolHandler.__init__(self, driverType)
		# driver.__init__(self)  # Executed by subclass

	def terminate(self):
		try:
			super().terminate()
		finally:
			# Make sure the device gets closed.
			self._dev.close()


MSG_XON = 0x11
MSG_XOFF = 0x13


class WTSRemoteDriver(RemoteDriver):
	timeout = 0.5

	def __init__(self, driverType: protocol.DriverType):
		super().__init__(driverType)
		self._connected = False
		try:
			self._dev = wtsVirtualChannel.WTSVirtualChannel(
				f"NVDA-{self._driverType.name}",
				onReceive=self._onReceive
			)
		except EnvironmentError:
			raise
		# Wait for RdPipe at the other end to send a XON
		for i in range(3):
			self._dev.waitForRead(self.timeout)
			if self._connected:
				break
		if self._connected:
			return
		self._dev.close()
		raise RuntimeError("No answer from remote system")

	@abstractmethod
	def _handleRemoteDisconnect(self):
		raise NotImplementedError()

	@classmethod
	def check(cls):
		return WTSIsRemoteSession()

	def _onReceive(self, message: bytes):
		if len(message) == 1:
			command = message[0]
			if command == MSG_XON:
				self._connected = True
				return
			elif command == MSG_XOFF:
				self._handleRemoteDisconnect()
				return
		super()._onReceive(message)
