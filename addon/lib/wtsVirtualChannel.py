from winAPI import wtsApi32
from hwIo.base import IoBase
from typing import Callable, Optional
from ctypes import byref, create_string_buffer, windll, WinError, memmove, sizeof, Structure, c_uint32
from ctypes.wintypes import HANDLE, DWORD, LPVOID, UINT
from serial.win32 import INVALID_HANDLE_VALUE

WTS_CHANNEL_OPTION_DYNAMIC = 0x00000001
WTS_CHANNEL_OPTION_DYNAMIC_PRI_REAL = 0x00000006
WTSVirtualFileHandle = 1
CHANNEL_CHUNK_LENGTH = 1600


class ChannelPduHeader(Structure):
	_fields_ = (
		("length", c_uint32),
		("flags", c_uint32),
	)


CHANNEL_PDU_LENGTH = CHANNEL_CHUNK_LENGTH +sizeof(ChannelPduHeader)


class WTSVirtualChannel(IoBase):
	wtsHandle: int

	def __init__(
		self,
		channelName: str,
		onReceive: Callable[[bytes], None],
		onReadError: Optional[Callable[[int], bool]] = None
	):
		wtsHandle = windll.wtsapi32.WTSVirtualChannelOpenEx(
			wtsApi32.WTS_CURRENT_SESSION,
			create_string_buffer(channelName.encode("ascii")),
			WTS_CHANNEL_OPTION_DYNAMIC | WTS_CHANNEL_OPTION_DYNAMIC_PRI_REAL
		)
		if wtsHandle == 0:
			raise WinError()
		self.wtsHandle = wtsHandle
		fileHandle = HANDLE()
		fileHandlePtr = LPVOID()
		len = DWORD()
		if windll.wtsapi32.WTSVirtualChannelQuery(
			wtsHandle,
			WTSVirtualFileHandle,
			byref(fileHandle),
			byref(len)
		):
			raise WinError()
		memmove(fileHandle, fileHandlePtr, sizeof(fileHandle))
		windll.wtsapi32.WTSFreeMemory(fileHandlePtr)
		super().__init__(
			fileHandle,
			onReceive,
			onReceiveSize=sizeof(ChannelPduHeader),
			onReadError=onReadError
		)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			if windll.wtsapi32.WTSVirtualChannelClose(self._file):
				raise WinError()
