# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os
from collections.abc import Callable, Iterator
from ctypes import (
	WinError,
	byref,
	c_ulong,
	sizeof,
	windll,
)
from ctypes.wintypes import DWORD, HANDLE
from enum import IntFlag
from glob import iglob

import winKernel
from appModuleHandler import processEntry32W
from hwIo.base import IoBase
from hwIo.ioThread import IoThread
from serial.win32 import (
	FILE_FLAG_OVERLAPPED,
	INVALID_HANDLE_VALUE,
	CreateFile,
)

PIPE_DIRECTORY = "\\\\.\\pipe\\"
RD_PIPE_GLOB_PATTERN = os.path.join(PIPE_DIRECTORY, "RdPipe_NVDA-*")
TH32CS_SNAPPROCESS = 0x00000002


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


class NamedPipeClient(IoBase):
	pipeProcessId: int | None = None
	pipeParentProcessId: int | None = None
	pipeMode: PipeMode
	pipeName: str

	def __init__(
		self,
		pipeName: str,
		onReceive: Callable[[bytes], None],
		onReceiveSize: int = MAX_PIPE_MESSAGE_SIZE,
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

	def close(self):
		super().close()
		if hasattr(self, "_file") and self._file is not INVALID_HANDLE_VALUE:
			winKernel.closeHandle(self._file)
			self._file = INVALID_HANDLE_VALUE
