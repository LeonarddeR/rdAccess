# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from ctypes import byref, Structure, sizeof, windll, WinError
from ctypes.wintypes import UINT, DWORD


class LastINPUTINFO(Structure):
	_fields_ = [
		('cbSize', UINT),
		('dwTime', DWORD),
	]

	def __init__(self):
		super().__init__
		self.cbSize = sizeof(LastINPUTINFO)


def getLastInputInfo() -> int:
	lastINPUTINFO = LastINPUTINFO()
	if not windll.user32.GetLastInputInfo(byref(lastINPUTINFO)):
		raise WinError()
	return lastINPUTINFO.dwTime


windll.kernel32.GetTickCount.restype = DWORD


def getTickCount() -> int:
	return windll.kernel32.GetTickCount()


def getTimeSinceInput() -> int:
	return getTickCount() - getLastInputInfo()
