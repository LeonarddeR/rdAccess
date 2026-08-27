# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for the version gates in lib.nvdaCompat."""

from __future__ import annotations

import importlib
import unittest

import buildVersion
from lib import nvdaCompat


class TestCapsLockSyncSupported(unittest.TestCase):
	"""CAPS_LOCK_SYNC_SUPPORTED reflects whether NVDA passes ``injected`` to raw key handlers,
	which it does from 2026.3 on.
	"""

	def setUp(self):
		self.addCleanup(self._reloadWithVersion, buildVersion.version_year, buildVersion.version_major)

	@staticmethod
	def _reloadWithVersion(year: int, major: int) -> bool:
		buildVersion.version_year = year
		buildVersion.version_major = major
		return importlib.reload(nvdaCompat).CAPS_LOCK_SYNC_SUPPORTED

	def test_unsupported_before_2026_3(self):
		self.assertFalse(self._reloadWithVersion(2026, 2))

	def test_supported_on_2026_3(self):
		self.assertTrue(self._reloadWithVersion(2026, 3))

	def test_supported_on_later_year_with_lower_major(self):
		"""The comparison is year-then-major, not major alone."""
		self.assertTrue(self._reloadWithVersion(2027, 1))
