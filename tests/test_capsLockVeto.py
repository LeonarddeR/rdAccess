# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for lib.capsLock.InjectedCapsLockVeto."""

from __future__ import annotations

import unittest
from unittest import mock

import keyboardHandler
import winUser
from extensionPoints import Decider
from lib.capsLock import InjectedCapsLockVeto

CAPS_LOCK_SCAN_CODE = 58
VK_A = 0x41


class TestInjectedCapsLockVeto(unittest.TestCase):
	"""The veto swallows exactly the caps lock events a focused remote desktop client feeds back
	into the system.

	Decisions go through a real ``extensionPoints.Decider`` with the keyword arguments NVDA 2026.3
	passes to raw key handlers, so a parameter name the handler does not accept surfaces as a
	wrong decision rather than being dropped silently.
	"""

	def setUp(self):
		self.enabled = True
		self.remoteProcessHasFocus = True
		self.veto = InjectedCapsLockVeto(
			isEnabled=lambda: self.enabled,
			remoteProcessHasFocus=lambda: self.remoteProcessHasFocus,
		)
		self.decider = Decider()
		self.decider.register(self.veto.decide)

	def _decide(self, vkCode: int = winUser.VK_CAPITAL, pressed: bool = True, injected: bool = True) -> bool:
		return self.decider.decide(
			vkCode=vkCode,
			scanCode=CAPS_LOCK_SCAN_CODE,
			extended=False,
			pressed=pressed,
			injected=injected,
		)

	def test_swallows_injected_caps_lock_press(self):
		self.assertFalse(self._decide())

	def test_swallows_injected_caps_lock_release(self):
		self.assertFalse(self._decide(pressed=False))

	def test_passes_physical_caps_lock(self):
		self.assertTrue(self._decide(injected=False))

	def test_passes_other_injected_keys(self):
		self.assertTrue(self._decide(vkCode=VK_A))

	def test_passes_keys_injected_by_nvda_itself(self):
		with mock.patch.object(keyboardHandler, "ignoreInjected", True):
			self.assertTrue(self._decide())

	def test_passes_when_synchronization_is_disabled(self):
		self.enabled = False
		self.assertTrue(self._decide())

	def test_passes_when_caps_lock_is_not_an_nvda_modifier(self):
		with mock.patch.object(keyboardHandler, "isNVDAModifierKey", return_value=False):
			self.assertTrue(self._decide())

	def test_passes_when_no_remote_process_has_focus(self):
		self.remoteProcessHasFocus = False
		self.assertTrue(self._decide())
