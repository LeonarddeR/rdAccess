import typing
import addonHandler
from winAPI import sessionTracking
from ctypes import WinError, c_bool, POINTER, byref, cast, c_void_p
from ctypes.wintypes import DWORD, LPWSTR
from driverHandler import Driver
from logHandler import log

if typing.TYPE_CHECKING:
	from . import protocol
	from . import wtsVirtualChannel
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib\\protocol")
	wtsVirtualChannel = addon.loadModule("lib\\wtsVirtualChannel")


class RemoteDriver(protocol.RemoteProtocolHandler, Driver):
	name = "remote"

	@classmethod
	def check(cls):
		ppBuffer = LPWSTR(None)
		pBytesReturned = DWORD(0)
		res = sessionTracking.WTSQuerySessionInformation(
			sessionTracking.WTS_CURRENT_SERVER_HANDLE,
			sessionTracking.WTS_CURRENT_SESSION,
			sessionTracking.WTS_INFO_CLASS.WTSIsRemoteSession,
			byref(ppBuffer),
			byref(pBytesReturned)
		)
		if not res:
			log.error(f"Couldn't check whether in a remote session: {WinError()}")
			return False
		try:
			return cast(ppBuffer, POINTER(c_bool)).contents.value
		finally:
			sessionTracking.WTSFreeMemory(cast(ppBuffer, c_void_p))

	def __init__(self):
		super().__init__(protocol.DriverType.BRAILLE)
		try:
			self._dev = wtsVirtualChannel.WTSVirtualChannel(
				f"NVDA-{self._driverType.name}",
				onReceive=self._onReceive
			)
		except EnvironmentError:
			raise

	def terminate(self):
		try:
			super().terminate()
		finally:
			self.close()
