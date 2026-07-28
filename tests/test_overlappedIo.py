# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Integration tests for overlapped I/O, driven over a real named pipe.

Each test connects the class under test to a pipe whose inbound buffer is far smaller than
the payload, so a write genuinely pends, and drives the peer end from a helper thread with
a fixed schedule. That makes "a read completes while a write is outstanding" reproducible
rather than incidental.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import threading
import time
import unittest
import unittest.mock
from ctypes import byref, c_void_p, create_string_buffer, windll
from ctypes.wintypes import DWORD, HANDLE, LPCWSTR

import winKernel
from hwIo.ioThread import IoThread
from lib.ioBase import OverlappedIoBase
from serial.win32 import FILE_FLAG_OVERLAPPED, CreateFile

PIPE_ACCESS_DUPLEX = 0x00000003
PIPE_BUFFER_SIZE = 1024
#: Large enough that the peer's inbound buffer cannot absorb it, so the write must pend.
PAYLOAD_SIZE = 256 * 1024
ERROR_IO_INCOMPLETE = 996

#: Seconds after the write starts at which the peer sends a byte, completing the client's read.
READ_AT = 0.3
#: Seconds after the write starts at which the peer drains, completing the client's write.
DRAIN_AT = 0.7
#: How long onReceive occupies the IO thread, delaying re-arming of the background read.
RECEIVE_DELAY = 0.15

_kernel32 = windll.kernel32
_kernel32.CreateNamedPipeW.restype = HANDLE
_kernel32.CreateNamedPipeW.argtypes = (LPCWSTR, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, c_void_p)

_pipeCounter = 0


def _uniquePipeName() -> str:
	global _pipeCounter
	_pipeCounter += 1
	return f"\\\\.\\pipe\\rdAccessTest_{os.getpid()}_{_pipeCounter}"


def _isPending(fileHandle: int, overlapped) -> bool:
	"""Whether the operation described by C{overlapped} has yet to complete."""
	transferred = DWORD()
	if _kernel32.GetOverlappedResult(HANDLE(fileHandle), byref(overlapped), byref(transferred), False):
		return False
	return ctypes.GetLastError() == ERROR_IO_INCOMPLETE


def _transferredBytes(fileHandle: int, overlapped) -> int:
	transferred = DWORD()
	if not _kernel32.GetOverlappedResult(HANDLE(fileHandle), byref(overlapped), byref(transferred), False):
		raise ctypes.WinError()
	return transferred.value


class OverlappedIoTestCase(unittest.TestCase):
	"""Base providing a connected pipe pair, an IO thread and a scripted peer."""

	def setUp(self):
		self.pipeName = _uniquePipeName()
		self.serverHandle = _kernel32.CreateNamedPipeW(
			self.pipeName,
			PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
			0,  # byte type, byte read mode, blocking
			1,  # a single instance
			PIPE_BUFFER_SIZE,
			PIPE_BUFFER_SIZE,
			0,
			None,
		)
		if self.serverHandle == HANDLE(-1).value:
			raise ctypes.WinError()
		self.ioThread = IoThread()
		self.ioThread.start()
		self.received: list[bytes] = []
		self.dev: OverlappedIoBase | None = None

	def tearDown(self):
		if self.dev is not None:
			with contextlib.suppress(OSError):
				self.dev.close()
		if self.serverHandle is not None:
			_kernel32.CloseHandle(HANDLE(self.serverHandle))
			self.serverHandle = None
		self.ioThread.stop()

	def connect(self, onReceive=None, access: int | None = None) -> OverlappedIoBase:
		if access is None:
			access = winKernel.GENERIC_READ | winKernel.GENERIC_WRITE
		clientHandle = CreateFile(
			self.pipeName,
			access,
			0,
			None,
			winKernel.OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED,
			None,
		)
		self.dev = OverlappedIoBase(
			clientHandle,
			onReceive if onReceive is not None else self._defaultOnReceive,
			onReceiveSize=64,
			ioThread=self.ioThread,
		)
		return self.dev

	def _defaultOnReceive(self, data: bytes):
		self.received.append(data)
		time.sleep(RECEIVE_DELAY)

	def peerWrite(self, data: bytes):
		transferred = DWORD()
		if not _kernel32.WriteFile(
			HANDLE(self.serverHandle),
			create_string_buffer(data, len(data)),
			DWORD(len(data)),
			byref(transferred),
			None,
		):
			raise ctypes.WinError()

	def closePeer(self):
		_kernel32.CloseHandle(HANDLE(self.serverHandle))
		self.serverHandle = None

	def peerDrain(self, size: int = PAYLOAD_SIZE):
		buffer = create_string_buffer(1 << 16)
		transferred = DWORD()
		total = 0
		while total < size:
			if not _kernel32.ReadFile(
				HANDLE(self.serverHandle),
				buffer,
				DWORD(1 << 16),
				byref(transferred),
				None,
			):
				raise ctypes.WinError()
			total += transferred.value

	def startPeer(self, schedule):
		"""Run C{schedule} on a helper thread, recording any exception for the test to surface."""
		self.peerError: BaseException | None = None

		def runner():
			try:
				schedule()
			except BaseException as e:  # noqa: BLE001
				self.peerError = e

		thread = threading.Thread(target=runner, daemon=True)
		thread.start()
		return thread

	def assertPeerSucceeded(self):
		if self.peerError is not None:
			raise AssertionError(f"The peer thread failed: {self.peerError!r}")


class PendingWriteTests(OverlappedIoTestCase):
	"""A write that is outstanding while a read on the same handle completes."""

	def _readThenDrainSchedule(self):
		def schedule():
			time.sleep(READ_AT)
			self.peerWrite(b"X")
			time.sleep(DRAIN_AT - READ_AT)
			self.peerDrain()

		return schedule

	def test_readCompletesWhileTheWriteIsStillPending(self):
		"""Harness guard: the arrangement really does deliver a read mid-write.

		Holds both before and after the write fix; without it the tests below could pass
		without ever exercising the race.
		"""
		observed: list[bool] = []

		def onReceive(data: bytes):
			self.received.append(data)
			assert self.dev is not None
			observed.append(_isPending(self.dev._writeFile, self.dev._writeOl))
			time.sleep(RECEIVE_DELAY)

		dev = self.connect(onReceive)
		self.startPeer(self._readThenDrainSchedule())
		dev.write(b"A" * PAYLOAD_SIZE)
		time.sleep(RECEIVE_DELAY * 2)

		self.assertPeerSucceeded()
		self.assertEqual(self.received, [b"X"])
		self.assertEqual(observed, [True], "the write had already completed when the read arrived")

	def test_writeDoesNotReturnUntilTheWriteCompletes(self):
		dev = self.connect()
		self.startPeer(self._readThenDrainSchedule())
		dev.write(b"A" * PAYLOAD_SIZE)

		self.assertFalse(
			_isPending(dev._writeFile, dev._writeOl),
			"write() returned while the write was still pending",
		)
		self.assertEqual(_transferredBytes(dev._writeFile, dev._writeOl), PAYLOAD_SIZE)
		self.assertPeerSucceeded()


class SyncReadTests(OverlappedIoTestCase):
	"""A blocking read issued from onReceive, as WTSVirtualChannel does mid-PDU."""

	def test_syncReadReturnsTheCompletePayload(self):
		trailer = b"trailing PDU chunk"
		finished = threading.Event()
		results: list[bytes] = []

		def onReceive(data: bytes):
			self.received.append(data)
			assert self.dev is not None
			try:
				results.append(self.dev._syncRead())
			finally:
				finished.set()

		self.connect(onReceive)

		def schedule():
			time.sleep(READ_AT)
			self.peerWrite(b"X")
			self.peerWrite(trailer)

		self.startPeer(schedule)

		self.assertTrue(finished.wait(5), "the blocking read never returned")
		self.assertPeerSucceeded()
		self.assertEqual(self.received, [b"X"])
		self.assertEqual(results, [trailer])

	def test_syncReadRaisesRatherThanReturningStaleData(self):
		"""A failed read must not hand back whatever the previous read left in the buffer."""
		finished = threading.Event()
		outcomes: list[object] = []

		def onReceive(data: bytes):
			self.received.append(data)
			assert self.dev is not None
			try:
				outcomes.append(self.dev._syncRead())
			except OSError as e:
				outcomes.append(e)
			finally:
				finished.set()

		dev = self.connect(onReceive)
		self.assertIsNotNone(dev)

		def schedule():
			time.sleep(READ_AT)
			self.peerWrite(b"X")
			# Break the pipe while the blocking read is outstanding, so the read fails.
			time.sleep(RECEIVE_DELAY)
			self.closePeer()

		self.startPeer(schedule)

		self.assertTrue(finished.wait(5), "the blocking read never returned")
		self.assertPeerSucceeded()
		self.assertEqual(self.received, [b"X"])
		self.assertEqual(len(outcomes), 1)
		self.assertIsInstance(
			outcomes[0],
			OSError,
			f"the failed read returned {outcomes[0]!r} instead of raising",
		)


class DeviceWiringTests(unittest.TestCase):
	"""The devices RDAccess opens must go through the overlapped-aware base."""

	def test_namedPipeClientUsesOverlappedIo(self):
		from lib.namedPipe import NamedPipeClient

		self.assertTrue(issubclass(NamedPipeClient, OverlappedIoBase))

	def test_wtsVirtualChannelUsesOverlappedIo(self):
		from lib.wtsVirtualChannel import WTSVirtualChannel

		self.assertTrue(issubclass(WTSVirtualChannel, OverlappedIoBase))

	def test_wtsVirtualChannelReadsThroughSyncRead(self):
		from lib.wtsVirtualChannel import WTSVirtualChannel

		self.assertIs(WTSVirtualChannel._read, OverlappedIoBase._syncRead)


class CloseTests(OverlappedIoTestCase):
	def test_closeReleasesEachHandleExactlyOnce(self):
		"""A repeated close must not hand the same handle value to CloseHandle twice.

		The value may have been reissued to unrelated code by then.
		"""
		dev = self.connect()
		closed: list[int] = []
		realCloseHandle = winKernel.closeHandle

		def spy(handle, *args):
			closed.append(int(handle))
			return realCloseHandle(handle, *args)

		with unittest.mock.patch.object(winKernel, "closeHandle", spy):
			dev.close()
			dev.close()
		self.dev = None

		duplicates = {handle for handle in closed if closed.count(handle) > 1}
		self.assertEqual(duplicates, set(), f"handles closed more than once: {duplicates}")


class WriteFailureTests(OverlappedIoTestCase):
	"""A write that is outstanding when the peer disappears."""

	def test_writeRaisesWhenThePeerClosesMidWrite(self):
		dev = self.connect()

		def schedule():
			time.sleep(READ_AT)
			self.closePeer()

		self.startPeer(schedule)
		with self.assertRaises(OSError):
			dev.write(b"A" * PAYLOAD_SIZE)
		self.assertPeerSucceeded()


if __name__ == "__main__":
	unittest.main()
