from winAPI import sessionTracking
from ctypes import WinError, c_bool, POINTER, byref, cast, c_void_p
from ctypes.wintypes import DWORD, LPWSTR
from logHandler import log


def WTSIsRemoteSession() -> bool:
	ppBuffer = LPWSTR(None)
	pBytesReturned = DWORD(0)
	res = sessionTracking.WTSQuerySessionInformation(
		sessionTracking.WTS_CURRENT_SERVER_HANDLE,
		sessionTracking.WTS_CURRENT_SESSION,
		sessionTracking.WTS_INFO_CLASS.WTSIsRemoteSession,
		byref(ppBuffer),
		byref(pBytesReturned)
	)
	if not res:
		log.error(f"Couldn't check whether in a remote session: {WinError()}")
		return False
	try:
		return cast(ppBuffer, POINTER(c_bool)).contents.value
	finally:
		sessionTracking.WTSFreeMemory(cast(ppBuffer, c_void_p))
