from hwIo.base import IoBase
from typing import Callable, Optional, Union
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
from enum import IntFlag, IntEnum


ERROR_PIPE_CONNECTED = 0x217


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


class NamedPipeBase(IoBase):
	pipeProcessId: int
	pipeMode: PipeMode = PipeMode.READMODE_BYTE | PipeMode.WAIT

	def __init__(
		self,
		fileHandle: Union[HANDLE, int],
		onReceive: Callable[[bytes], None],
		onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
		onReadError: Optional[Callable[[int], bool]] = None,
		pipeMode: PipeMode = PipeMode.READMODE_BYTE,
	):
		super().__init__(fileHandle, onReceive, onReceiveSize=onReceiveSize, onReadError=onReadError)

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
		pipeMode: PipeMode = PipeMode.READMODE_BYTE,
		pipeOpenMode: PipeOpenMode = PipeOpenMode.ACCESS_DUPLEX | PipeOpenMode.OVERLAPPED | PipeOpenMode.FIRST_PIPE_INSTANCE
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
			fileHandle,
			onReceive,
			onReadError=onReadError,
			pipeMode=pipeMode,
		)
	def _asyncRead(self):
		if not self._connected:
			res = windll.ConnectNamedPipe(fileHandle, ol)
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
		pipeMode: PipeMode = PipeMode.READMODE_BYTE,
		maxInstances: int = 1,
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
			fileHandle,
			onReceive,
			onReadError=onReadError,
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
