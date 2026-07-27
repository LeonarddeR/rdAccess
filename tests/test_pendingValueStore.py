# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for PendingValueStore, the coalescing store for values awaiting application."""

from __future__ import annotations

import unittest

from lib.protocol import PendingValueStore
from logHandler import log

_MISSING = object()


class PendingValueStoreTests(unittest.TestCase):
	def setUp(self):
		self.store = PendingValueStore()
		self.applied: list[tuple[str, object]] = []

	def _apply(self, key: str, value: object):
		self.applied.append((key, value))

	def test_pushSignalsDrainOnlyWhenEmpty(self):
		self.assertTrue(self.store.push("a", 1))
		self.assertFalse(self.store.push("a", 2))
		self.assertFalse(self.store.push("b", 3))

	def test_getReturnsPendingValue(self):
		self.store.push("a", 1)
		self.assertEqual(self.store.get("a", _MISSING), 1)

	def test_getReturnsDefaultWhenAbsent(self):
		self.assertIs(self.store.get("a", _MISSING), _MISSING)

	def test_drainAppliesLatestValuePerKey(self):
		self.store.push("a", 1)
		self.store.push("a", 2)
		self.store.drain(self._apply)
		self.assertEqual(self.applied, [("a", 2)])

	def test_drainEmptiesTheStore(self):
		self.store.push("a", 1)
		self.store.drain(self._apply)
		self.assertIs(self.store.get("a", _MISSING), _MISSING)
		self.assertTrue(self.store.push("a", 2))

	def test_valueRemainsVisibleWhileBeingApplied(self):
		self.store.push("a", 1)
		seen: list[object] = []

		def _applyAndPeek(key: str, _value: object):
			seen.append(self.store.get(key, _MISSING))

		self.store.drain(_applyAndPeek)
		self.assertEqual(seen, [1])

	def test_valuePushedDuringApplyIsAppliedBySameDrain(self):
		self.store.push("a", 1)

		def _applyAndPush(key: str, value: object):
			self.applied.append((key, value))
			if value == 1:
				self.store.push("a", 2)

		self.store.drain(_applyAndPush)
		self.assertEqual(self.applied, [("a", 1), ("a", 2)])

	def test_drainAppliesAllKeys(self):
		self.store.push("a", 1)
		self.store.push("b", 2)
		self.store.drain(self._apply)
		self.assertEqual(sorted(self.applied), [("a", 1), ("b", 2)])

	def test_applyErrorIsLoggedAndSkipped(self):
		self.store.push("a", 1)
		self.store.push("b", 2)
		log.records.clear()

		def _applyOrRaise(key: str, value: object):
			if key == "a":
				raise RuntimeError("intentional apply failure")
			self.applied.append((key, value))

		self.store.drain(_applyOrRaise)
		self.assertEqual(self.applied, [("b", 2)])
		self.assertIs(self.store.get("a", _MISSING), _MISSING)
		self.assertTrue(any(level == "error" for level, _msg in log.records))


if __name__ == "__main__":
	unittest.main()
