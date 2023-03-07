from winAPI import sessionTracking
from ctypes import WinError, c_int, POINTER, byref, cast, c_void_p, windll
from ctypes.wintypes import DWORD, LPWSTR
from logHandler import log
from enum import IntEnum

WF_CURRENT_SESSION = -1


class SessionType(IntEnum):
	CONSOLE = 0
	ICA = 1
	RDP = 2


def getRemoteSessionType() -> SessionType:
	t = _WTSClientProtocolType()
	if t == 0:
		try:
			t = windll.wfapi.WFGetActiveProtocol(WF_CURRENT_SESSION)
		except OSError:
			pass
	return SessionType(t)


def _WTSClientProtocolType() -> int:
	ppBuffer = LPWSTR(None)
	pBytesReturned = DWORD(0)
	res = sessionTracking.WTSQuerySessionInformation(
		sessionTracking.WTS_CURRENT_SERVER_HANDLE,
		sessionTracking.WTS_CURRENT_SESSION,
		sessionTracking.WTS_INFO_CLASS.WTSClientProtocolType,
		byref(ppBuffer),
		byref(pBytesReturned)
	)
	if not res:
		log.error(f"Couldn't check whether in a remote session: {WinError()}")
		return False
	try:
		return cast(ppBuffer, POINTER(c_int)).contents.value
	finally:
		sessionTracking.WTSFreeMemory(cast(ppBuffer, c_void_p))
