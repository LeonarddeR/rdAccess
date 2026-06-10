# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for utility behaviour of RemoteProtocolHandler:
_safeWait, _pickle, _unpickle, terminate, _queueFunctionOnMainThread.
"""

from __future__ import annotations

import gc
import unittest
import weakref

import queueHandler  # noqa: E402 — must follow tests import so stubs are installed
from baseObject import AutoPropertyObject  # noqa: E402 — same reason

from tests._fakes import FakeHandlerBase  # bootstrap runs via tests/__init__ import

# ---------------------------------------------------------------------------
# Module-level helper required by test 5 (must be picklable by reference).
# ---------------------------------------------------------------------------


class _PickleProbe(AutoPropertyObject):
	"""AutoPropertyObject whose invalidateCache sets a flag for inspection."""

	cachePropertiesByDefault = True

	def __init__(self):
		super().__init__()
		self.cacheInvalidated = False

	def invalidateCache(self):
		self.cacheInvalidated = True
		super().invalidateCache()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


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


class TestPickleUnpickle(unittest.TestCase):
	"""Tests for RemoteProtocolHandler._pickle and _unpickle."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_roundtrip_plain_structure(self):
		"""_unpickle(_pickle(obj)) reproduces the original plain structure."""
		original = {"key": b"bytes_value", "name": "hello", "count": 42}
		raw = self.handler._pickle(original)
		restored = self.handler._unpickle(raw)
		self.assertEqual(restored, original)

	def test_unpickle_calls_invalidate_cache_on_auto_property_object(self):
		"""_unpickle calls invalidateCache on AutoPropertyObject results."""
		probe = _PickleProbe()
		raw = self.handler._pickle(probe)
		result = self.handler._unpickle(raw)
		self.assertIsInstance(result, _PickleProbe)
		self.assertTrue(result.cacheInvalidated)

	def test_unpickle_does_not_call_invalidate_cache_on_plain_objects(self):
		"""_unpickle does not call invalidateCache on non-AutoPropertyObject results."""
		# dict has no invalidateCache; if _unpickle tried to call it this would raise.
		data = {"x": 1}
		raw = self.handler._pickle(data)
		result = self.handler._unpickle(raw)
		self.assertEqual(result, data)


class TestTerminate(unittest.TestCase):
	"""Tests for RemoteProtocolHandler.terminate."""

	def test_terminate_closes_device(self):
		"""After terminate(), the underlying IO device is closed."""
		handler = FakeHandlerBase()
		# Seed the cache directly to avoid needing a registered attribute receiver.
		handler._attributeValueProcessor._values[b"k"] = 1
		handler.terminate()
		self.assertTrue(handler._dev.closed)

	def test_terminate_shuts_down_executor(self):
		"""After terminate(), the background executor is shut down."""
		handler = FakeHandlerBase()
		handler.terminate()
		self.assertTrue(handler._bgExecutor.isShutdown)

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
