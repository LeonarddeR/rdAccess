# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Client side of the caps lock synchronization: keeps caps lock presses that a remote desktop
client feeds back into the system away from the local NVDA and the local keyboard state."""

from __future__ import annotations

from collections.abc import Callable

import keyboardHandler
import winUser


class InjectedCapsLockVeto:
	"""Swallows caps lock key events that a focused remote desktop client feeds back into the
	system. Applies while caps lock is configured as an NVDA modifier key; key events injected by
	NVDA itself pass through.

	:param isEnabled: Whether caps lock synchronization is switched on.
	:param remoteProcessHasFocus: Whether a remote desktop client process currently has focus.
	"""

	def __init__(self, isEnabled: Callable[[], bool], remoteProcessHasFocus: Callable[[], bool]):
		self._isEnabled = isEnabled
		self._remoteProcessHasFocus = remoteProcessHasFocus

	def decide(self, vkCode: int, extended: bool, injected: bool | None = None) -> bool:
		"""Handler for ``inputCore.decide_handleRawKey``; ``False`` swallows the key event.

		NVDA builds that do not pass ``injected`` get plain pass-through.
		"""
		return not (
			vkCode == winUser.VK_CAPITAL
			and injected
			and not keyboardHandler.ignoreInjected
			and self._isEnabled()
			and keyboardHandler.isNVDAModifierKey(vkCode, extended)
			and self._remoteProcessHasFocus()
		)
