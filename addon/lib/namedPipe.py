# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os
from collections.abc import Callable, Iterator
from ctypes import (
	POINTER,
	GetLastError,
	WinError,
	byref,
	c_ulong,
	sizeof,
	windll,
)
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPCWSTR, LPVOID
from enum import IntFlag
from glob import iglob

import winKernel
from appModuleHandler import processEntry32W
from hwIo.base import IoBase
from hwIo.ioThread import IoThread
from logHandler import log
from serial.win32 import (
	ERROR_IO_PENDING,
	FILE_FLAG_OVERLAPPED,
	INVALID_HANDLE_VALUE,
	LPOVERLAPPED,
	OVERLAPPED,
	CreateFile,
)

from .ioThreadEx import IoThreadEx

ERROR_INVALID_HANDLE = 0x6
ERROR_PIPE_CONNECTED = 0x217
ERROR_PIPE_BUSY = 0xE7
PIPE_DIRECTORY = "\\\\.\\pipe\\"
RD_PIPE_GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")
SECURE_DESKTOP_GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "NVDA_SD-*")
SECURITY_DESCRIPTOR_REVISION = 1
TH32CS_SNAPPROCESS = 0x00000002
windll.advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
	LPCWSTR,
	DWORD,
	POINTER(LPVOID),
	POINTER(DWORD),
]
windll.advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = BOOL
windll.kernel32.CreateNamedPipeW.restype = HANDLE
windll.kernel32.CreateNamedPipeW.argtypes = (
	LPCWSTR,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	DWORD,
	POINTER(winKernel.SECURITY_ATTRIBUTES),
)
windll.kernel32.ConnectNamedPipe.restype = BOOL
windll.kernel32.ConnectNamedPipe.argtypes = (HANDLE, LPOVERLAPPED)
windll.kernel32.DisconnectNamedPipe.restype = BOOL
windll.kernel32.DisconnectNamedPipe.argtypes = (HANDLE,)


def getParentProcessId(processId: int) -> int | None:
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
	REJECT_REMOTE_CLIENTS = 0x00000008


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
	pipeProcessId: int | None = None
	pipeParentProcessId: int | None = None
	pipeMode: PipeMode
	pipeName: str

	def __init__(
		self,
		pipeName: str,
		fileHandle: HANDLE | int,
		onReceive: Callable[[bytes], None],
		onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
		onReadError: Callable[[int], bool] | None = None,
		ioThread: IoThread | None = None,
		pipeMode: PipeMode = PipeMode.READMODE_BYTE,
	):
		self.pipeName = pipeName
		self.pipeMode = pipeMode
		super().__init__(
			fileHandle,
			onReceive,
			onReceiveSize=onReceiveSize,
			onReadError=onReadError,
			ioThread=ioThread,
		)

	def _get_isAlive(self) -> bool:
		return self.pipeName in getNamedPipes()


class NamedPipeServer(NamedPipeBase):
	_connected: bool = False
	_onConnected: Callable[[bool], None] | None = None
	_waitObject: HANDLE | None = None
	_connectOl: OVERLAPPED | None = None
	_ioThreadRef: Callable[[], IoThreadEx]

	def __init__(
		self,
		pipeName: str,
		onReceive: Callable[[bytes], None],
		onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
		onConnected: Callable[[bool], None] | None = None,
		ioThreadEx: IoThreadEx | None = None,
		pipeMode: PipeMode = PipeMode.READMODE_BYTE | PipeMode.REJECT_REMOTE_CLIENTS,
		pipeOpenMode: PipeOpenMode = (
			PipeOpenMode.ACCESS_DUPLEX | PipeOpenMode.OVERLAPPED | PipeOpenMode.FIRST_PIPE_INSTANCE
		),
		maxInstances: int = 1,
		stringSecurityDescriptor: str | None = None,
	):
		log.debug(f"Initializing named pipe: Name={pipeName}")
		if stringSecurityDescriptor:
			p_security_descriptor = LPVOID()
			if not windll.advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
				stringSecurityDescriptor,
				SECURITY_DESCRIPTOR_REVISION,
				byref(p_security_descriptor),
				None,
			):
				raise WinError()
			sa = winKernel.SECURITY_ATTRIBUTES(
				lpSecurityDescriptor=p_security_descriptor,
				bInheritHandle=False,
			)
		else:
			sa = None
		fileHandle = windll.kernel32.CreateNamedPipeW(
			pipeName,
			pipeOpenMode,
			pipeMode,
			maxInstances,
			onReceiveSize,
			onReceiveSize,
			0,
			byref(sa) if sa else None,
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
			ioThread=ioThreadEx,
			pipeMode=pipeMode,
		)

	def _handleConnect(self):
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
		try:
			self._ioThreadRef().waitForSingleObjectWithCallback(self._recvEvt, self._handleConnectCallback)
		except OSError as e:
			error = e.winerror
			log.error(
				f"Error while calling RegisterWaitForSingleObject for {self.pipeName}: {WinError(error)}"
			)
			self._ioDone(error, 0, byref(ol))

	def _handleConnectCallback(self, _parameter: int, _timerOrWaitFired: bool):
		log.debug(f"Event set for {self.pipeName}")
		numberOfBytes = DWORD()
		log.debug(f"Getting overlapped result for {self.pipeName} after wait for event")
		if not windll.kernel32.GetOverlappedResult(
			self._file, byref(self._connectOl), byref(numberOfBytes), False
		):
			error = GetLastError()
			log.debug(f"Error while getting overlapped result for {self.pipeName}: {WinError(error)}")
			self._ioDone(error, 0, byref(self._connectOl))
			return
		self._connected = True
		log.debug("Succesfully connected {self.pipeName}, handling post connection logic")
		clientProcessId = c_ulong()
		if not windll.kernel32.GetNamedPipeClientProcessId(HANDLE(self._file), byref(clientProcessId)):
			raise WinError()
		self.pipeProcessId = clientProcessId.value
		self.pipeParentProcessId = getParentProcessId(self.pipeProcessId)
		self._initialRead()
		if self._onConnected is not None:
			self._onConnected(True)
		log.debug("End of handleConnectCallback for {self.pipeName}")
		self._connectOl = None

	def _onReadError(self, error: int):
		winErr = WinError(error)
		log.debug(f"Read error: {winErr}")
		if isinstance(winErr, BrokenPipeError):
			self.disconnect()
			self._initialRead()
			return True
		return False

	def _asyncRead(self, _param: int | None = None):
		if not self._connected:
			# _handleConnect will call _asyncRead when it is finished.
			self._handleConnect()
		else:
			super()._asyncRead()

	def disconnect(self):
		if not self._connected:
			return
		if not windll.kernel32.DisconnectNamedPipe(self._file):
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
		"""Hack, we don't want _ioDone to set itself to None."""
		pass


class NamedPipeClient(NamedPipeBase):
	def __init__(
		self,
		pipeName: str,
		onReceive: Callable[[bytes], None],
		onReadError: Callable[[int], bool] | None = None,
		ioThread: IoThread | None = None,
		pipeMode: PipeMode = PipeMode.READMODE_BYTE,
	):
		fileHandle = CreateFile(
			pipeName,
			winKernel.GENERIC_READ | winKernel.GENERIC_WRITE,
			0,
			None,
			winKernel.OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED,
			None,
		)
		if fileHandle == INVALID_HANDLE_VALUE:
			raise WinError()
		try:
			if pipeMode:
				dwPipeMode = DWORD(pipeMode)
				if not windll.kernel32.SetNamedPipeHandleState(fileHandle, byref(dwPipeMode), 0, 0):
					raise WinError()
			serverProcessId = c_ulong()
			if not windll.kernel32.GetNamedPipeServerProcessId(HANDLE(fileHandle), byref(serverProcessId)):
				raise WinError()
			self.pipeProcessId = serverProcessId.value
			self.pipeParentProcessId = getParentProcessId(self.pipeProcessId)
		except Exception:
			winKernel.closeHandle(fileHandle)
			raise
		super().__init__(
			pipeName,
			fileHandle,
			onReceive,
			onReadError=onReadError,
			ioThread=ioThread,
			pipeMode=pipeMode,
		)

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)
			self._file = INVALID_HANDLE_VALUE
