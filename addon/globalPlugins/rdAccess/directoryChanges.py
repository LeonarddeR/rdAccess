# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import sys
import os.path
from hwIo.ioThread import IoThread
from extensionPoints import Action
import winKernel
from serial.win32 import FILE_FLAG_OVERLAPPED, CreateFile, INVALID_HANDLE_VALUE, OVERLAPPED, LPOVERLAPPED
from enum import IntFlag, IntEnum
from ctypes import windll, WinError, sizeof, byref, create_string_buffer
from struct import unpack, calcsize
import queueHandler


FILE_FLAG_BACKUP_SEMANTICS = 0x02000000


class FileNotifyFilter(IntFlag):
	FILE_NOTIFY_CHANGE_FILE_NAME = 0x1
	FILE_NOTIFY_CHANGE_DIR_NAME = 0x2
	FILE_NOTIFY_CHANGE_ATTRIBUTES = 0X4
	FILE_NOTIFY_CHANGE_SIZE = 0x8
	FILE_NOTIFY_CHANGE_LAST_WRITE = 0X10
	FILE_NOTIFY_CHANGE_LAST_ACCESS = 0x20
	FILE_NOTIFY_CHANGE_CREATION = 0x40
	FILE_NOTIFY_CHANGE_SECURITY = 0x100


class FileNotifyInformationAction(IntEnum):
	FILE_ACTION_ADDED = 0x1
	FILE_ACTION_REMOVED = 0x2
	FILE_ACTION_MODIFIED = 0x3
	FILE_ACTION_RENAMED_OLD_NAME = 0x4
	FILE_ACTION_RENAMED_NEW_NAME = 0x5


class DirectoryWatcher(IoThread):
	directoryChanged: Action

	def __init__(
			self,
			directory: str,
			notifyFilter: FileNotifyFilter = FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME,
			watchSubtree: bool = False
	):
		super().__init__()
		self._watching = False
		self._directory = directory
		self._notifyFilter = notifyFilter
		self._watchSubtree = watchSubtree
		self.directoryChanged = Action()
		dirHandle = CreateFile(
			directory,
			winKernel.GENERIC_READ,
			winKernel.FILE_SHARE_READ | winKernel.FILE_SHARE_WRITE | winKernel.FILE_SHARE_DELETE,
			None,
			winKernel.OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED | FILE_FLAG_BACKUP_SEMANTICS,
			None
		)
		if dirHandle == INVALID_HANDLE_VALUE:
			raise WinError()
		self._dirHandle = dirHandle
		self._buffer = create_string_buffer(4096)
		self._overlapped = OVERLAPPED()

	def start(self):
		if self._watching:
			return
		super().start()
		self.queueAsApc(self._asyncWatch)
		self._watching = True

	def stop(self):
		if not self._watching:
			return
		self._watching = False
		try:
			if hasattr(self, "_dirHandle") and not windll.kernel32.CancelIoEx(
				self._dirHandle,
				byref(self._overlapped)
			):
				raise WinError()
		finally:
			super().stop()

	def __del__(self):
		try:
			self.stop()
		finally:
			if hasattr(self, "_dirHandle"):
				winKernel.closeHandle(self._dirHandle)

	def _asyncWatch(self, param: int = 0):
		res = windll.kernel32.ReadDirectoryChangesW(
			self._dirHandle,
			byref(self._buffer),
			sizeof(self._buffer),
			self._watchSubtree,
			self._notifyFilter,
			None,
			byref(self._overlapped),
			self.queueAsCompletionRoutine(self._ioDone, self._overlapped)
		)
		if not res:
			raise WinError()

	def _ioDone(self, error, numberOfBytes: int, overlapped: LPOVERLAPPED):
		if not self._watching:
			# We stopped watching
			return
		if numberOfBytes == 0:
			raise RuntimeError("No bytes received, probably internal buffer overflow")
		if error != 0:
			raise WinError(error)
		data = self._buffer.raw[:numberOfBytes]
		self._asyncWatch()
		queueHandler.queueFunction(queueHandler.eventQueue, self._handleChanges, data)

	def _handleChanges(self, data: bytes):
		nextOffset = 0
		while True:
			fileNameLength = int.from_bytes(
				# fileNameLength is the third DWORD in the FILE_NOTIFY_INFORMATION struct
				data[nextOffset + 8: nextOffset + 12],
				byteorder=sys.byteorder,
				signed=False
			)
			format = f"@3I{fileNameLength}s"
			nextOffset, action, fileNameLength, fileNameBytes = unpack(
				format,
				data[nextOffset: nextOffset + calcsize(format)]
			)
			fileName = fileNameBytes.decode("utf-16")
			self.directoryChanged.notify(
				action=FileNotifyInformationAction(action),
				fileName=os.path.join(self._directory, fileName)
			)
			if nextOffset == 0:
				break
