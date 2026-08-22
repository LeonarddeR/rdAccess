# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for utility behaviour of RemoteProtocolHandler:
_safeWait, terminate, _queueFunctionOnMainThread.
"""

from __future__ import annotations

import gc
import threading
import unittest
import weakref

import queueHandler  # noqa: E402 — must follow tests import so stubs are installed

from tests._fakes import FakeHandlerBase  # bootstrap runs via tests/__init__ import


class TestSafeWait(unittest.TestCase):
	"""Tests for RemoteProtocolHandler._safeWait."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_returns_true_immediately_when_predicate_already_true(self):
		"""_safeWait returns True without consulting waitForRead when predicate is True on entry."""
		result = self.handler._safeWait(lambda: True, timeout=1.0)
		self.assertTrue(result)
		# FakeIo.waitForReadResults is empty and returns False by default;
		# a True result here proves waitForRead was never the deciding factor.

	def test_returns_false_when_predicate_stays_false_and_read_returns_false(self):
		"""_safeWait returns False quickly when predicate is always False and waitForRead says False."""
		# FakeIo.waitForReadResults is empty so waitForRead always returns False immediately.
		result = self.handler._safeWait(lambda: False, timeout=0.05)
		self.assertFalse(result)

	def test_returns_true_when_predicate_becomes_true_after_successful_read(self):
		"""_safeWait returns True once a scripted successful read lets the predicate flip."""
		# Script exactly one successful read result.
		self.handler._dev.waitForReadResults = [True]

		calls = []

		def _predicate() -> bool:
			calls.append(len(calls))
			# False on first call, True on second (after the scripted read).
			return len(calls) >= 2

		result = self.handler._safeWait(_predicate, timeout=1.0)
		self.assertTrue(result)
		self.assertGreaterEqual(len(calls), 2)

	def test_raises_when_called_on_the_devices_io_thread(self):
		"""Waiting on the device's own IO thread can never be satisfied and must fail fast."""
		raised: list[RuntimeError] = []

		def _callSafeWait():
			try:
				self.handler._safeWait(lambda: False, timeout=0.05)
			except RuntimeError as e:
				raised.append(e)

		thread = threading.Thread(target=_callSafeWait)
		self.handler._dev._ioThreadRef = weakref.ref(thread)
		thread.start()
		thread.join(2.0)
		self.assertEqual(len(raised), 1)

	def test_does_not_raise_on_other_threads_when_io_thread_known(self):
		"""With a known IO thread, callers on any other thread wait normally."""
		ioThread = threading.Thread(target=lambda: None)
		self.handler._dev._ioThreadRef = weakref.ref(ioThread)
		result = self.handler._safeWait(lambda: False, timeout=0.05)
		self.assertFalse(result)


class TestTerminate(unittest.TestCase):
	"""Tests for RemoteProtocolHandler.terminate."""

	def test_terminate_closes_device(self):
		"""After terminate(), the underlying IO device is closed."""
		handler = FakeHandlerBase()
		# Seed the cache directly to avoid needing a registered attribute receiver.
		handler._attributeValueProcessor._values[b"k"] = 1
		handler.terminate()
		self.assertTrue(handler._dev.closed)

	def test_terminate_clears_attribute_cache(self):
		"""After terminate(), previously stored attribute values are gone from the cache."""
		handler = FakeHandlerBase()
		# Seed the cache directly to avoid needing a registered attribute receiver.
		handler._attributeValueProcessor._values[b"k"] = 1
		handler.terminate()
		with self.assertRaises(KeyError):
			handler._attributeValueProcessor.getValue(b"k", fallBackToDefault=False)


class TestGarbageCollection(unittest.TestCase):
	"""The handler stores hold only a weak reference to their owner (see #59).

	Before the #59 refactor the handler registries kept strong references to bound
	methods (a regression from #54), creating an instance↔store cycle. This test
	documents the restored behavior: a terminated handler is collectable.
	"""

	def test_handler_collectable_after_terminate(self):
		handler = FakeHandlerBase()
		handler.terminate()
		ref = weakref.ref(handler)
		del handler
		gc.collect()
		self.assertIsNone(ref(), "Handler instance should be garbage collectable after terminate()")


class TestQueueFunctionOnMainThread(unittest.TestCase):
	"""Tests for RemoteProtocolHandler._queueFunctionOnMainThread."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_function_not_called_before_pump(self):
		"""The queued function must not execute before pumpAll() is called."""
		calls: list[tuple] = []

		def _record(*args, **kwargs):
			calls.append((args, kwargs))

		self.handler._queueFunctionOnMainThread(_record, 1, k=2)
		self.assertEqual(calls, [], "Function must not run synchronously; call pumpAll first")

	def test_function_called_once_with_correct_args_after_pump(self):
		"""After pumpAll() the function runs exactly once with the forwarded arguments."""
		calls: list[tuple] = []

		def _record(*args, **kwargs):
			calls.append((args, kwargs))

		self.handler._queueFunctionOnMainThread(_record, 1, k=2)
		queueHandler.pumpAll()

		self.assertEqual(len(calls), 1)
		args, kwargs = calls[0]
		self.assertEqual(args, (1,))
		self.assertEqual(kwargs, {"k": 2})

	def test_exception_in_queued_function_does_not_propagate(self):
		"""pumpAll() must not raise even if the queued function itself raises."""

		def _boom():
			raise RuntimeError("intentional error")

		self.handler._queueFunctionOnMainThread(_boom)
		# Must not raise.
		try:
			queueHandler.pumpAll()
		except Exception as exc:  # noqa: BLE001
			self.fail(f"pumpAll() raised unexpectedly: {exc}")


if __name__ == "__main__":
	unittest.main()
