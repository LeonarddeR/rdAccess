from winAPI import _wtsApi32 as wtsApi32
from hwIo.base import IoBase, _isDebug
from typing import Callable, Optional
from ctypes import (
	byref,
	create_string_buffer,
	windll,
	WinError,
	POINTER,
	sizeof,
	Structure,
	c_uint32,
	GetLastError
)
from ctypes.wintypes import HANDLE, DWORD
from serial.win32 import INVALID_HANDLE_VALUE, ERROR_IO_PENDING
from logHandler import log
import winKernel

WTS_CHANNEL_OPTION_DYNAMIC = 0x00000001
WTS_CHANNEL_OPTION_DYNAMIC_PRI_REAL = 0x00000006
WTSVirtualFileHandle = 1
CHANNEL_CHUNK_LENGTH = 1600
CHANNEL_FLAG_FIRST = 0x01
CHANNEL_FLAG_LAST = 0x02
CHANNEL_FLAG_ONLY = CHANNEL_FLAG_FIRST | CHANNEL_FLAG_LAST


class ChannelPduHeader(Structure):
	_fields_ = (
		("length", c_uint32),
		("flags", c_uint32),
	)


CHANNEL_PDU_LENGTH = CHANNEL_CHUNK_LENGTH + sizeof(ChannelPduHeader)


class WTSVirtualChannel(IoBase):
	_rawOutput: bool

	def __init__(
		self,
		channelName: str,
		onReceive: Callable[[bytes], None],
		onReadError: Optional[Callable[[int], bool]] = None,
		rawOutput=False
	):
		wtsHandle = windll.wtsapi32.WTSVirtualChannelOpenEx(
			wtsApi32.WTS_CURRENT_SESSION,
			create_string_buffer(channelName.encode("ascii")),
			WTS_CHANNEL_OPTION_DYNAMIC | WTS_CHANNEL_OPTION_DYNAMIC_PRI_REAL
		)
		if wtsHandle == 0:
			raise WinError()
		try:
			fileHandlePtr = POINTER(HANDLE)()
			length = DWORD()
			if not windll.wtsapi32.WTSVirtualChannelQuery(
				wtsHandle,
				WTSVirtualFileHandle,
				byref(fileHandlePtr),
				byref(length)
			):
				raise WinError()
			try:
				assert length.value == sizeof(HANDLE)
				curProc = winKernel.GetCurrentProcess()
				fileHandle = winKernel.DuplicateHandle(
					curProc,
					fileHandlePtr.contents.value,
					curProc,
					0,
					False,
					winKernel.DUPLICATE_SAME_ACCESS
				)
			finally:
				windll.wtsapi32.WTSFreeMemory(fileHandlePtr)
		finally:
			if not windll.wtsapi32.WTSVirtualChannelClose(wtsHandle):
				raise WinError()
		self._rawOutput = rawOutput
		super().__init__(
			fileHandle,
			onReceive,
			onReceiveSize=CHANNEL_PDU_LENGTH,
			onReadError=onReadError
		)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)

	def _notifyReceive(self, data: bytes):
		if self._rawOutput:
			return super()._notifyReceive(data)
		buffer = bytearray()
		dataToProcess = data
		while True:
			header = ChannelPduHeader.from_buffer_copy(dataToProcess[:sizeof(ChannelPduHeader)])
			if not buffer:
				assert header.flags & CHANNEL_FLAG_FIRST
			buffer.extend(dataToProcess[sizeof(ChannelPduHeader):])
			if header.flags & CHANNEL_FLAG_LAST:
				assert len(buffer) == header.length
				return super()._notifyReceive(bytes(buffer))
			dataToProcess = self._read()

	def _read(self) -> bytes:
		byteData = DWORD()
		if not windll.kernel32.ReadFile(
			self._file,
			self._readBuf,
			self._readSize,
			byref(byteData),
			byref(self._readOl)
		):
			if GetLastError() != ERROR_IO_PENDING:
				if _isDebug():
					log.debug(f"Read failed: {WinError()}")
				raise WinError()
			windll.kernel32.GetOverlappedResult(self._file, byref(self._readOl), byref(byteData), True)
		return self._readBuf.raw[:byteData.value]
