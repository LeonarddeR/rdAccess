# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for cross-thread serialization of RemoteProtocolHandler.sendMessage."""

from __future__ import annotations

import threading
import time
import unittest

from lib.protocol.messages import RdMessageType

from tests._fakes import FakeHandlerBase, FakeIo

THREAD_COUNT = 8
MESSAGES_PER_THREAD = 25


class _ConcurrencyProbeIo(FakeIo):
	"""FakeIo that records how many threads are inside write() at once."""

	def __init__(self):
		super().__init__()
		self._counterLock = threading.Lock()
		self._activeWriters = 0
		self.maxConcurrentWriters = 0

	def write(self, data: bytes):
		with self._counterLock:
			self._activeWriters += 1
			self.maxConcurrentWriters = max(self.maxConcurrentWriters, self._activeWriters)
		# Widen the race window; sleep releases the GIL like a pending WriteFile would.
		time.sleep(0.001)
		super().write(data)
		with self._counterLock:
			self._activeWriters -= 1


class SendMessageThreadSafetyTests(unittest.TestCase):
	def _hammer(self, handler: FakeHandlerBase) -> list[Exception]:
		errors: list[Exception] = []

		def worker(workerIndex: int):
			try:
				for i in range(MESSAGES_PER_THREAD):
					handler.sendMessage(RdMessageType.SPEAK, sequence=[f"{workerIndex}-{i}"])
			except Exception as e:  # noqa: BLE001
				errors.append(e)

		threads = [threading.Thread(target=worker, args=(n,)) for n in range(THREAD_COUNT)]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		return errors

	def _assertSerialized(self, handler: FakeHandlerBase):
		dev = handler._dev
		errors = self._hammer(handler)
		self.assertEqual(errors, [])
		self.assertEqual(len(dev.writes), THREAD_COUNT * MESSAGES_PER_THREAD)
		self.assertEqual(
			dev.maxConcurrentWriters,
			1,
			"sendMessage allowed concurrent writes to the device",
		)

	def test_jsonWritesAreSerializedAcrossThreads(self):
		handler = FakeHandlerBase()
		handler._dev = _ConcurrencyProbeIo()
		handler._sendJson = True
		self._assertSerialized(handler)

	def test_legacyWritesAreSerializedAcrossThreads(self):
		handler = FakeHandlerBase()
		handler._dev = _ConcurrencyProbeIo()
		self.assertFalse(handler._sendJson)
		self._assertSerialized(handler)


if __name__ == "__main__":
	unittest.main()
