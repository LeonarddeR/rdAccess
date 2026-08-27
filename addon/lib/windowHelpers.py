# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Helpers to query top level window state."""

from __future__ import annotations

from ctypes import WINFUNCTYPE, windll
from ctypes.wintypes import HWND

import winUser

dll = windll.user32

GetShellWindow = WINFUNCTYPE(None)(("GetShellWindow", dll))
"""
Retrieves a handle to the Shell's desktop window.

.. seealso::
	https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getshellwindow
"""
GetShellWindow.restype = HWND
GetShellWindow.argtypes = ()


def getShellProcessId() -> int | None:
	"""The id of the process owning the shell's desktop window."""
	shellWindow = GetShellWindow()
	if not shellWindow:
		return None
	return winUser.getWindowThreadProcessID(shellWindow)[0] or None
