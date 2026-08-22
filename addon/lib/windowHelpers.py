# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Helpers to query top level window state."""

from __future__ import annotations

from ctypes import POINTER, WINFUNCTYPE, Structure, byref, sizeof, windll
from ctypes.wintypes import BOOL, DWORD, HMONITOR, HWND, RECT

import winUser
from winBindings import user32

dll = windll.user32

MONITOR_DEFAULTTONEAREST = 2


class MONITORINFO(Structure):
	"""
	Contains information about a display monitor.

	.. seealso::
		https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-monitorinfo
	"""

	_fields_ = (
		("cbSize", DWORD),
		("rcMonitor", RECT),
		("rcWork", RECT),
		("dwFlags", DWORD),
	)


LPMONITORINFO = POINTER(MONITORINFO)

GetShellWindow = WINFUNCTYPE(None)(("GetShellWindow", dll))
"""
Retrieves a handle to the Shell's desktop window.

.. seealso::
	https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getshellwindow
"""
GetShellWindow.restype = HWND
GetShellWindow.argtypes = ()

MonitorFromWindow = WINFUNCTYPE(None)(("MonitorFromWindow", dll))
"""
Retrieves a handle to the display monitor that has the largest area of intersection with the
bounding rectangle of a specified window.

.. seealso::
	https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-monitorfromwindow
"""
MonitorFromWindow.restype = HMONITOR
MonitorFromWindow.argtypes = (
	HWND,  # hwnd: Handle to the window of interest
	DWORD,  # dwFlags: Determines the return value if the window does not intersect any display monitor
)

GetMonitorInfo = WINFUNCTYPE(None)(("GetMonitorInfoW", dll))
"""
Retrieves information about a display monitor.

.. seealso::
	https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmonitorinfow
"""
GetMonitorInfo.restype = BOOL
GetMonitorInfo.argtypes = (
	HMONITOR,  # hMonitor: Handle to the display monitor of interest
	LPMONITORINFO,  # lpmi: MONITORINFO that receives information about the specified display monitor
)


def getShellProcessId() -> int | None:
	"""The id of the process owning the shell's desktop window."""
	shellWindow = GetShellWindow()
	if not shellWindow:
		return None
	return winUser.getWindowThreadProcessID(shellWindow)[0] or None


def isForegroundWindowFullScreen() -> bool:
	"""Whether the foreground window covers the entire monitor it is on.

	False for maximized windows, which only cover the monitor's work area.
	"""
	hwnd = winUser.getForegroundWindow()
	windowRect = RECT()
	if not user32.GetWindowRect(hwnd, byref(windowRect)):
		return False
	monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
	monitorInfo = MONITORINFO(cbSize=sizeof(MONITORINFO))
	if not GetMonitorInfo(monitor, byref(monitorInfo)):
		return False
	monitorRect = monitorInfo.rcMonitor
	return (
		windowRect.left <= monitorRect.left
		and windowRect.top <= monitorRect.top
		and windowRect.right >= monitorRect.right
		and windowRect.bottom >= monitorRect.bottom
	)
