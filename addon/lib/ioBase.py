# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

from __future__ import annotations

from ctypes import GetLastError, WinError, byref
from ctypes.wintypes import DWORD

import winBindings.kernel32
import winKernel
from hwIo.base import IoBase, _isDebug
from logHandler import log
from serial.win32 import ERROR_IO_PENDING, OVERLAPPED, ReadFile


class OverlappedIoBase(IoBase):
	"""IoBase that waits on a dedicated manual-reset event per overlapped operation and
	raises when one fails.
	"""

	#: The write event this instance created, or C{None} when the base class supplied one.
	_writeEvent: int | None = None
	#: Overlapped structure and event used by L{_syncRead}.
	_syncReadOl: OVERLAPPED
	_syncReadEvent: int | None = None
	_closed: bool = False

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if not self._writeOl.hEvent:
			self._writeEvent = winKernel.createEvent(manualReset=True)
			self._writeOl.hEvent = self._writeEvent
		self._syncReadOl = OVERLAPPED()
		self._syncReadEvent = winKernel.createEvent(manualReset=True)
		self._syncReadOl.hEvent = self._syncReadEvent

	def close(self):
		"""Release the device, absorbing any repeat call rather than passing it on."""
		if self._closed:
			return
		self._closed = True
		super().close()
		if self._writeEvent is not None:
			winKernel.closeHandle(self._writeEvent)
			self._writeEvent = None
		if self._syncReadEvent is not None:
			winKernel.closeHandle(self._syncReadEvent)
			self._syncReadEvent = None

	def write(self, data: bytes):
		if not isinstance(data, bytes):
			raise TypeError("Expected argument 'data' to be of type 'bytes'")
		if _isDebug():
			log.debug(f"Write: {data!r}")
		size, buffer = self._prepareWriteBuffer(data)
		if winBindings.kernel32.WriteFile(self._writeFile, buffer, size, None, byref(self._writeOl)):
			return
		if GetLastError() != ERROR_IO_PENDING:
			if _isDebug():
				log.debug(f"Write failed: {WinError()}")
			raise WinError()
		transferred = DWORD()
		if not winBindings.kernel32.GetOverlappedResult(
			self._writeFile,
			byref(self._writeOl),
			byref(transferred),
			True,
		):
			if _isDebug():
				log.debug(f"Pending write failed: {WinError()}")
			raise WinError()

	def _syncRead(self) -> bytes:
		"""Read into L{_readBuf} and block until the read completes.

		Call this only where the background read is not armed, i.e. from within onReceive.
		"""
		transferred = DWORD()
		if not ReadFile(
			self._file,
			self._readBuf,
			self._readSize,
			byref(transferred),
			byref(self._syncReadOl),
		):
			if GetLastError() != ERROR_IO_PENDING:
				if _isDebug():
					log.debug(f"Read failed: {WinError()}")
				raise WinError()
			if not winBindings.kernel32.GetOverlappedResult(
				self._file,
				byref(self._syncReadOl),
				byref(transferred),
				True,
			):
				if _isDebug():
					log.debug(f"Pending read failed: {WinError()}")
				raise WinError()
		return self._readBuf.raw[: transferred.value]
