from hwIo.ioThread import IoThread
from typing import Callable, Iterator, Optional, Union
from ctypes import (
	byref,
	c_ulong,
	GetLastError,
	windll,
	WinError,
)
from ctypes.wintypes import HANDLE, DWORD
from serial.win32 import (
	CreateFile,
	ERROR_IO_PENDING,
	FILE_FLAG_OVERLAPPED,
	INVALID_HANDLE_VALUE,
	OVERLAPPED,
)
import winKernel
from enum import IntFlag
from .ioBaseEx import IoBaseEx
import os
from glob import iglob


ERROR_PIPE_CONNECTED = 0x217
ERROR_PIPE_BUSY = 0xE7
PIPE_DIRECTORY = "\\\\?\\pipe\\"
GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")


def getNamedPipes() -> Iterator[str]:
	yield from iglob(GLOB_PATTERN)


class PipeMode(IntFlag):
	READMODE_BYTE = 0x00000000
	READMODE_MESSAGE = 0x00000002
	WAIT = 0x00000000
	NOWAIT = 0x00000001


class PipeOpenMode(IntFlag):
	ACCESS_DUPLEX = 0x00000003
	ACCESS_INBOUND = 0x00000001
	ACCESS_OUTBOUND = 0x00000002
	FIRST_PIPE_INSTANCE = 0x00080000
	WRITE_THROUGH = 0x80000000
	OVERLAPPED = FILE_FLAG_OVERLAPPED
	WRITE_DAC = 0x00040000
	WRITE_OWNER = 0x00080000
	ACCESS_SYSTEM_SECURITY = 0x01000000


MAX_PIPE_MESSAGE_SIZE = 1024 * 64


class NamedPipeBase(IoBaseEx):
	pipeProcessId: int
	pipeMode: PipeMode = PipeMode.READMODE_BYTE | PipeMode.WAIT
	pipeName: str

	def __init__(
			self,
			pipeName: str,
			fileHandle: Union[HANDLE, int],
			onReceive: Callable[[bytes], None],
			onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
			onReadError: Optional[Callable[[int], bool]] = None,
			ioThread: Optional[IoThread] = None,
			pipeMode: PipeMode = PipeMode.READMODE_BYTE,
	):
		self.pipeName = pipeName
		super().__init__(
			fileHandle,
			onReceive,
			onReceiveSize=onReceiveSize,
			onReadError=onReadError,
			ioThread=ioThread
		)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)


class NamedPipeServer(NamedPipeBase):

	def __init__(
			self,
			pipeName: str,
			onReceive: Callable[[bytes], None],
			onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
			onReadError: Optional[Callable[[int], bool]] = None,
			ioThread: Optional[IoThread] = None,
			pipeMode: PipeMode = PipeMode.READMODE_BYTE,
			pipeOpenMode: PipeOpenMode = (
				PipeOpenMode.ACCESS_DUPLEX
				| PipeOpenMode.OVERLAPPED
				| PipeOpenMode.FIRST_PIPE_INSTANCE
			),
			maxInstances: int = 1
	):
		fileHandle = windll.kernel32.CreateNamedPipeW(
			pipeName,
			pipeOpenMode,
			pipeMode,
			maxInstances,
			onReceiveSize,
			onReceiveSize,
			0,
			None
		)
		if fileHandle == INVALID_HANDLE_VALUE:
			raise WinError()
		self._connected = False
		ol = OVERLAPPED()
		ol.hEvent = winKernel.createEvent()
		self._connectOl = ol
		super().__init__(
			pipeName,
			fileHandle,
			onReceive,
			onReadError=onReadError,
			ioThread=ioThread,
			pipeMode=pipeMode,
		)

	def _asyncRead(self):
		if not self._connected:
			res = windll.ConnectNamedPipe(self._file, self._connectOl)
			if res == 0:
				error = GetLastError()
				if error not in (ERROR_IO_PENDING, ERROR_PIPE_CONNECTED):
					raise WinError(error)
		super()._asyncRead()


class NamedPipeClient(NamedPipeBase):

	def __init__(
			self,
			pipeName: str,
			onReceive: Callable[[bytes], None],
			onReadError: Optional[Callable[[int], bool]] = None,
			ioThread: Optional[IoThread] = None,
			pipeMode: PipeMode = PipeMode.READMODE_BYTE
	):
		fileHandle = CreateFile(
			pipeName,
			winKernel.GENERIC_READ | winKernel.GENERIC_WRITE,
			0,
			None,
			winKernel.OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED,
			None
		)
		if fileHandle == INVALID_HANDLE_VALUE:
			raise WinError()
		super().__init__(
			pipeName,
			fileHandle,
			onReceive,
			onReadError=onReadError,
			ioThread=ioThread,
			pipeMode=pipeMode,
		)
		if pipeMode:
			dwPipeMode = DWORD(pipeMode)
			if not windll.kernel32.SetNamedPipeHandleState(fileHandle, byref(dwPipeMode), 0, 0):
				raise WinError()
		serverProcessId = c_ulong()
		if not windll.kernel32.GetNamedPipeServerProcessId(HANDLE(fileHandle), byref(serverProcessId)):
			raise WinError()
		self.pipeProcessId = serverProcessId.value

	def _get_isAlive(self) -> bool:
		return self.pipeName in getNamedPipes()
