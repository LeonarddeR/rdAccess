# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from hwIo.ioThread import IoThread
from typing import Callable, Iterator, Optional, Union
from ctypes import (
	WINFUNCTYPE,
	byref,
	c_ulong,
	GetLastError,
	POINTER,
	sizeof,
	windll,
	WinError,
)
from ctypes.wintypes import BOOL, BOOLEAN, HANDLE, DWORD, LPCWSTR, LPVOID
from serial.win32 import (
	CreateFile,
	ERROR_IO_PENDING,
	FILE_FLAG_OVERLAPPED,
	INVALID_HANDLE_VALUE,
	LPOVERLAPPED,
	OVERLAPPED,
)
import winKernel
from enum import IntFlag
import os
from glob import iglob
from appModuleHandler import processEntry32W
from hwIo.base import IoBase
from logHandler import log

ERROR_INVALID_HANDLE = 0x6
ERROR_PIPE_CONNECTED = 0x217
ERROR_PIPE_BUSY = 0xE7
WT_EXECUTEINWAITTHREAD = 0x00000004
WT_EXECUTELONGFUNCTION = 0x00000010
WT_EXECUTEONLYONCE = 0x00000008
PIPE_DIRECTORY = "\\\\?\\pipe\\"
RD_PIPE_GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")
SECURE_DESKTOP_GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "NVDA_SD-*")
TH32CS_SNAPPROCESS = 0x00000002
WaitOrTimerCallback = WINFUNCTYPE(None, LPVOID, BOOLEAN)
windll.kernel32.CreateNamedPipeW.restype = HANDLE
windll.kernel32.CreateNamedPipeW.argtypes = (
	LPCWSTR,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	POINTER(winKernel.SECURITY_ATTRIBUTES)
)
windll.kernel32.ConnectNamedPipe.restype = BOOL
windll.kernel32.ConnectNamedPipe.argtypes = (HANDLE, LPOVERLAPPED)
windll.kernel32.DisconnectNamedPipe.restype = BOOL
windll.kernel32.DisconnectNamedPipe.argtypes = (HANDLE,)
windll.kernel32.RegisterWaitForSingleObject.restype = BOOL
windll.kernel32.RegisterWaitForSingleObject.argtypes = (POINTER(HANDLE), HANDLE, WaitOrTimerCallback, LPVOID, DWORD, DWORD)


def getParentProcessId(processId: int) -> Optional[int]:
	FSnapshotHandle = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
	try:
		FProcessEntry32 = processEntry32W()
		FProcessEntry32.dwSize = sizeof(processEntry32W)
		ContinueLoop = windll.kernel32.Process32FirstW(FSnapshotHandle, byref(FProcessEntry32))
		while ContinueLoop:
			if FProcessEntry32.th32ProcessID == processId:
				return FProcessEntry32.th32ParentProcessID
			ContinueLoop = windll.kernel32.Process32NextW(FSnapshotHandle, byref(FProcessEntry32))
		else:
			return None
	finally:
		windll.kernel32.CloseHandle(FSnapshotHandle)


def getNamedPipes() -> Iterator[str]:
	yield from iglob(os.path.join(PIPE_DIRECTORY, "*"))


def getRdPipeNamedPipes() -> Iterator[str]:
	yield from iglob(RD_PIPE_GLOB_PATTERN)


def getSecureDesktopNamedPipes() -> Iterator[str]:
	yield from iglob(SECURE_DESKTOP_GLOB_PATTERN)


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
	pipeProcessId: Optional[int] = None
	pipeParentProcessId: Optional[int] = None
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

	def _get_isAlive(self) -> bool:
		return self.pipeName in getNamedPipes()


class NamedPipeServer(NamedPipeBase):
	_connected: bool = False
	_onConnected: Optional[Callable[[bool], None]] = None
	_waitObject: Optional[HANDLE] = None
	_connectOl: Optional[OVERLAPPED] = None
	_handleConnectCallbackWotc: Optional[WaitOrTimerCallback] = None

	def __init__(
			self,
			pipeName: str,
			onReceive: Callable[[bytes], None],
			onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
			onConnected: Optional[Callable[[bool], None]] = None,
			ioThread: Optional[IoThread] = None,
			pipeMode: PipeMode = PipeMode.READMODE_BYTE,
			pipeOpenMode: PipeOpenMode = (
				PipeOpenMode.ACCESS_DUPLEX
				| PipeOpenMode.OVERLAPPED
				| PipeOpenMode.FIRST_PIPE_INSTANCE
			),
			maxInstances: int = 1
	):
		log.debug(f"Initializing named pipe: Name={pipeName}")
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
		log.debug(f"Initialized named pipe: Name={pipeName}, handle={fileHandle}")
		self._onConnected = onConnected
		super().__init__(
			pipeName,
			fileHandle,
			onReceive,
			onReadError=self._onReadError,
			ioThread=ioThread,
			pipeMode=pipeMode,
		)

	def _handleConnect(self):
		self._handleConnectCallbackWotc = WaitOrTimerCallback(self._handleConnectCallback)
		self._connectOl = ol = OVERLAPPED()
		ol.hEvent = self._recvEvt
		log.debug(f"Connecting server end of named pipe: Name={self.pipeName}")
		connectRes = windll.kernel32.ConnectNamedPipe(self._file, byref(ol))
		error: int = GetLastError()
		if error == ERROR_PIPE_CONNECTED:
			log.debug(f"Server end of named pipe {self.pipeName} already connected")
			windll.kernel32.SetEvent(self._recvEvt)
		else:
			if not connectRes and error != ERROR_IO_PENDING:
				log.error(f"Error while calling ConnectNamedPipe for {self.pipeName}: {WinError(error)}")
				self._ioDone(error, 0, byref(ol))
				return
			log.debug(f"Named pipe {self.pipeName} pending client connection")
			self._waitObject = HANDLE()
			waitRes = windll.kernel32.RegisterWaitForSingleObject(byref(self._waitObject), self._recvEvt, self._handleConnectCallbackWotc, None, winKernel.INFINITE, WT_EXECUTEINWAITTHREAD | WT_EXECUTELONGFUNCTION | WT_EXECUTEONLYONCE)
			if not waitRes:
				error = GetLastError()
				log.error(f"Error while calling RegisterWaitForSingleObject for {self.pipeName}: {WinError(error)}")
				self._ioDone(error, 0, byref(ol))

	def _handleConnectCallback(self, parameter, timerOrWaitFired):
		try:
			assert timerOrWaitFired == 0
			log.debug(f"Event set for {self.pipeName}")
			numberOfBytes = DWORD()
			log.debug(f"Getting overlapped result for {self.pipeName} after wait for event")
			if not windll.kernel32.GetOverlappedResult(self._file, byref(self._connectOl), byref(numberOfBytes), False):
				error = GetLastError()
				log.debugWarning(f"Error while getting overlapped result for {self.pipeName}: {WinError(error)}")
				self._ioDone(error, 0, byref(self._connectOl))
				return
			self._connected = True
			log.debug("Succesfully connected {self.pipeName}, handling post connection logic")
			clientProcessId = c_ulong()
			if not windll.kernel32.GetNamedPipeClientProcessId(HANDLE(self._file), byref(clientProcessId)):
				raise WinError()
			self.pipeProcessId = clientProcessId.value
			self.pipeParentProcessId = getParentProcessId(self.pipeProcessId)
			if self._onConnected is not None:
				self._onConnected(True)
			log.debug("End of handleConnectCallback for {self.pipeName}")
			self._initialRead()
		finally:
			self._ioThreadRef().queueAsApc(self._cleanupHandleConnect)

	def _cleanupHandleConnect(self, param: Optional[int] = None):
		if self._waitObject is None:
			return
		windll.kernel32.UnregisterWaitEx(self._waitObject, INVALID_HANDLE_VALUE)
		self._waitObject = None
		self._connectOl = None
		self._handleConnectCallbackWotc = None

	def _onReadError(self, error: int):
		import tones
		tones.beep(440, 30)
		winErr = WinError(error)
		if isinstance(winErr, BrokenPipeError):
			self.disconnect()
			self._initialRead()
			return True
		return False

	def _asyncRead(self, param: Optional[int] = None):
		if not self._connected:
			# _handleConnect will call _asyncRead when it is finished.
			self._handleConnect()
		else:
			super()._asyncRead()

	def disconnect(self):
		if not 			windll.kernel32.DisconnectNamedPipe(self._file):
			raise WinError()
		self._connected = False
		self.pipeProcessId = None
		self.pipeParentProcessId = None
		if self._onConnected:
			self._onConnected(False)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			self.disconnect()
			self._onConnected = None
			winKernel.closeHandle(self._file)
			self._file = INVALID_HANDLE_VALUE

	@property
	def _ioDone(self):
		return super()._ioDone

	@_ioDone.setter
	def _ioDone(self, value):
		"""Hack, we don't want _ioDone to set itself to None.
		"""
		pass


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
		self.pipeParentProcessId = getParentProcessId(self.pipeProcessId)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)
			self._file = INVALID_HANDLE_VALUE
