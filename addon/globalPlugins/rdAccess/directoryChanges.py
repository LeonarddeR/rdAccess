# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Watches a directory for file name changes.

Change notifications are delivered as a bare "something changed" signal rather
than parsed per-file events: on the pipe file system, events that occur between
one ``ReadDirectoryChangesW`` completion and the next call are silently dropped
by the kernel, so consumers must rescan the directory anyway to get a reliable
view.
"""

from ctypes import WinError, byref, create_string_buffer, sizeof, windll
from enum import IntFlag

import queueHandler
import winKernel
from extensionPoints import Action
from hwIo.ioThread import IoThread
from logHandler import log
from serial.win32 import (
	FILE_FLAG_OVERLAPPED,
	INVALID_HANDLE_VALUE,
	LPOVERLAPPED,
	OVERLAPPED,
	CreateFile,
)

FILE_FLAG_BACKUP_SEMANTICS = 0x02000000


class FileNotifyFilter(IntFlag):
	FILE_NOTIFY_CHANGE_FILE_NAME = 0x1
	FILE_NOTIFY_CHANGE_DIR_NAME = 0x2
	FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x4
	FILE_NOTIFY_CHANGE_SIZE = 0x8
	FILE_NOTIFY_CHANGE_LAST_WRITE = 0x10
	FILE_NOTIFY_CHANGE_LAST_ACCESS = 0x20
	FILE_NOTIFY_CHANGE_CREATION = 0x40
	FILE_NOTIFY_CHANGE_SECURITY = 0x100


class DirectoryWatcher(IoThread):
	directoryChanged: Action

	def __init__(
		self,
		directory: str,
		notifyFilter: FileNotifyFilter = FileNotifyFilter.FILE_NOTIFY_CHANGE_FILE_NAME,
		watchSubtree: bool = False,
	):
		super().__init__()
		self._watching = False
		self._notifyQueued = False
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
			None,
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

	def stop(self, timeout: float | None = None):
		if not self._watching:
			return
		self._watching = False
		try:
			if hasattr(self, "_dirHandle") and not windll.kernel32.CancelIoEx(
				self._dirHandle,
				byref(self._overlapped),
			):
				raise WinError()
		finally:
			super().stop(timeout)

	def __del__(self):
		try:
			self.stop()
		finally:
			if hasattr(self, "_dirHandle"):
				winKernel.closeHandle(self._dirHandle)

	def _asyncWatch(self, _param: int = 0):
		res = windll.kernel32.ReadDirectoryChangesW(
			self._dirHandle,
			byref(self._buffer),
			sizeof(self._buffer),
			self._watchSubtree,
			self._notifyFilter,
			None,
			byref(self._overlapped),
			self.queueAsCompletionRoutine(self._ioDone, self._overlapped),
		)
		if not res:
			raise WinError()

	def _ioDone(self, error, numberOfBytes: int, _overlapped: LPOVERLAPPED):  # type: ignore
		if not self._watching:
			# We stopped watching
			return
		if error != 0:
			raise WinError(error)
		if numberOfBytes == 0:
			log.debugWarning("Directory change notification buffer overflowed, changes were dropped")
		self._asyncWatch()
		if not self._notifyQueued:
			self._notifyQueued = True
			queueHandler.queueFunction(queueHandler.eventQueue, self._notifyDirectoryChanged)

	def _notifyDirectoryChanged(self):
		self._notifyQueued = False
		self.directoryChanged.notify()
