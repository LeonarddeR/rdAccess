# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for RemoteProtocolHandler.terminate."""

from __future__ import annotations

import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from tests._fakes import FakeHandlerBase

TERMINATE_TIMEOUT = 2.0


class TerminateTests(unittest.TestCase):
	def test_terminateDoesNotBlockOnStuckExecutorTask(self):
		handler = FakeHandlerBase()
		handler._bgExecutor = ThreadPoolExecutor(4, thread_name_prefix="testRemoteHandler")
		release = threading.Event()
		try:
			handler._bgExecutor.submit(release.wait)
			terminated = threading.Event()

			def doTerminate():
				handler.terminate()
				terminated.set()

			terminateThread = threading.Thread(target=doTerminate, daemon=True)
			terminateThread.start()
			self.assertTrue(
				terminated.wait(TERMINATE_TIMEOUT),
				"terminate() blocked on a stuck background executor task",
			)
			self.assertTrue(handler._dev.closed)
		finally:
			release.set()


if __name__ == "__main__":
	unittest.main()
