# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from winAPI import _wtsApi32 as wtsApi32
from hwIo.base import _isDebug, IoBase
from hwIo.ioThread import IoThread
from typing import Callable, Optional
from ctypes import (
    byref,
    c_int,
    cdll,
    c_void_p,
    create_string_buffer,
    windll,
    WinError,
    POINTER,
    sizeof,
    Structure,
    c_uint32,
    GetLastError,
)
from ctypes.wintypes import BOOL, HANDLE, DWORD, LPWSTR
from serial.win32 import INVALID_HANDLE_VALUE, ERROR_IO_PENDING
from logHandler import log
import winKernel

WTS_CHANNEL_OPTION_DYNAMIC = 0x00000001
WTS_CHANNEL_OPTION_DYNAMIC_PRI_HIGH = 0x00000004
WTSVirtualFileHandle = 1
CHANNEL_CHUNK_LENGTH = 1600
CHANNEL_FLAG_FIRST = 0x01
CHANNEL_FLAG_LAST = 0x02
CHANNEL_FLAG_ONLY = CHANNEL_FLAG_FIRST | CHANNEL_FLAG_LAST
SM_REMOTESESSION = 0x1000


class ChannelPduHeader(Structure):
    _fields_ = (
        ("length", c_uint32),
        ("flags", c_uint32),
    )


CHANNEL_PDU_LENGTH = CHANNEL_CHUNK_LENGTH + sizeof(ChannelPduHeader)


try:
    vdp_rdpvcbridge = cdll.vdp_rdpvcbridge
except OSError:
    WTSVirtualChannelOpenEx = windll.wtsapi32.WTSVirtualChannelOpenEx
    WTSVirtualChannelQuery = windll.wtsapi32.WTSVirtualChannelQuery
    WTSVirtualChannelClose = windll.wtsapi32.WTSVirtualChannelClose
    GetSystemMetrics = windll.user32.GetSystemMetrics
else:
    WTSVirtualChannelOpenEx = vdp_rdpvcbridge.VDP_VirtualChannelOpenEx
    WTSVirtualChannelQuery = vdp_rdpvcbridge.VDP_VirtualChannelQuery
    # Slightly hacky but effective
    wtsApi32.WTSFreeMemory = vdp_rdpvcbridge.VDP_FreeMemory
    wtsApi32.WTSFreeMemory.argtypes = (
        c_void_p,  # [in] PVOID pMemory
    )
    wtsApi32.WTSFreeMemory.restype = None
    WTSVirtualChannelClose = vdp_rdpvcbridge.VDP_VirtualChannelClose
    wtsApi32.WTSQuerySessionInformation = vdp_rdpvcbridge.VDP_QuerySessionInformationW
    wtsApi32.WTSQuerySessionInformation.argtypes = (
        HANDLE,  # [in] HANDLE hServer
        DWORD,  # [ in] DWORD SessionId
        c_int,  # [ in]  WTS_INFO_CLASS WTSInfoClass,
        POINTER(LPWSTR),  # [out] LPWSTR * ppBuffer,
        POINTER(DWORD),  # [out] DWORD * pBytesReturned
    )
    wtsApi32.WTSQuerySessionInformation.restype = BOOL  # On Failure, the return value is zero.
    GetSystemMetrics = vdp_rdpvcbridge.VDP_GetSystemMetrics


def getRemoteSessionMetrics() -> bool:
    return bool(GetSystemMetrics(SM_REMOTESESSION))


class WTSVirtualChannel(IoBase):
    _rawOutput: bool

    def __init__(
        self,
        channelName: str,
        onReceive: Callable[[bytes], None],
        onReadError: Optional[Callable[[int], bool]] = None,
        ioThread: Optional[IoThread] = None,
        rawOutput=False,
    ):
        wtsHandle = WTSVirtualChannelOpenEx(
            wtsApi32.WTS_CURRENT_SESSION,
            create_string_buffer(channelName.encode("ascii")),
            WTS_CHANNEL_OPTION_DYNAMIC | WTS_CHANNEL_OPTION_DYNAMIC_PRI_HIGH,
        )
        if wtsHandle == 0:
            raise WinError()
        try:
            fileHandlePtr = POINTER(HANDLE)()
            length = DWORD()
            if not WTSVirtualChannelQuery(
                wtsHandle, WTSVirtualFileHandle, byref(fileHandlePtr), byref(length)
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
                    winKernel.DUPLICATE_SAME_ACCESS,
                )
            finally:
                wtsApi32.WTSFreeMemory(fileHandlePtr)
        finally:
            if not WTSVirtualChannelClose(wtsHandle):
                raise WinError()
        self._rawOutput = rawOutput
        super().__init__(
            fileHandle,
            onReceive,
            onReceiveSize=CHANNEL_PDU_LENGTH,
            onReadError=onReadError,
            ioThread=ioThread,
        )

    def close(self):
        super().close()
        if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
            winKernel.closeHandle(self._file)
            self._file = INVALID_HANDLE_VALUE

    def _notifyReceive(self, data: bytes):
        if self._rawOutput:
            return super()._notifyReceive(data)
        buffer = bytearray()
        dataToProcess = data
        while True:
            header = ChannelPduHeader.from_buffer_copy(
                dataToProcess[: sizeof(ChannelPduHeader)]
            )
            if not buffer:
                assert header.flags & CHANNEL_FLAG_FIRST
            buffer.extend(dataToProcess[sizeof(ChannelPduHeader) :])
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
            byref(self._readOl),
        ):
            if GetLastError() != ERROR_IO_PENDING:
                if _isDebug():
                    log.debug(f"Read failed: {WinError()}")
                raise WinError()
            windll.kernel32.GetOverlappedResult(
                self._file, byref(self._readOl), byref(byteData), True
            )
        return self._readBuf.raw[: byteData.value]
