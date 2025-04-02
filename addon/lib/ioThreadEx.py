# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import threading
from collections.abc import Callable
from ctypes import (
	POINTER,
	WINFUNCTYPE,
	GetLastError,
	WinError,
	addressof,
	byref,
	windll,
)
from ctypes.wintypes import BOOL, BOOLEAN, DWORD, HANDLE, LPVOID
from inspect import ismethod

import hwIo.ioThread
import winKernel
from extensionPoints.util import AnnotatableWeakref, BoundMethodWeakref
from logHandler import log
from serial.win32 import ERROR_IO_PENDING

WT_EXECUTEINWAITTHREAD = 0x4
WT_EXECUTELONGFUNCTION = 0x10
WT_EXECUTEONLYONCE = 0x8
WaitOrTimerCallback = WINFUNCTYPE(None, LPVOID, BOOLEAN)
WaitOrTimerCallbackIdT = int
WaitOrTimerCallbackT = Callable[[int, bool], None]
WaitOrTimerCallbackStoreT = dict[
	WaitOrTimerCallbackIdT,
	tuple[
		int,
		HANDLE,
		BoundMethodWeakref[WaitOrTimerCallbackT] | AnnotatableWeakref[WaitOrTimerCallbackT],
		WaitOrTimerCallbackIdT,
	],
]
windll.kernel32.RegisterWaitForSingleObject.restype = BOOL
windll.kernel32.RegisterWaitForSingleObject.argtypes = (
	POINTER(HANDLE),
	HANDLE,
	WaitOrTimerCallback,
	LPVOID,
	DWORD,
	DWORD,
)


class IoThreadEx(hwIo.ioThread.IoThread):
	"""
	IoThreadEx is an extended implementation of the hwIo.ioThread.IoThread class, providing
	additional functionality for handling asynchronous wait operations with callbacks.

	"""

	_waitOrTimerCallbackStore: WaitOrTimerCallbackStoreT = {}

	@WaitOrTimerCallback
	def _internalWaitOrTimerCallback(param: WaitOrTimerCallbackIdT, timerOrWaitFired: bool):
		(
			threadIdent,
			waitObject,
			reference,
			actualParam,
		) = IoThreadEx._waitOrTimerCallbackStore.pop(param, (0, 0, None, 0))
		threadInst: IoThreadEx = threading._active.get(threadIdent)
		if not isinstance(threadInst, IoThreadEx):
			log.error("Internal WaitOrTimerCallback called from unknown thread")
			return

		if reference is None:
			log.error(
				f"Internal WaitOrTimerCallback called with param {param}, but no such wait object in store"
			)
			return
		function = reference()
		if not function:
			log.debugWarning(
				f"Not executing queued WaitOrTimerCallback {param}:{reference.funcName} "
				f"with param {actualParam} "
				"because reference died"
			)
			return

		try:
			function(actualParam, bool(timerOrWaitFired))
		except Exception:
			log.error(
				f"Error in WaitOrTimerCallback function {function!r} with id {param} queued to IoThread",
				exc_info=True,
			)
		finally:
			threadInst.queueAsApc(threadInst._postWaitOrTimerCallback, waitObject)

	@staticmethod
	def _postWaitOrTimerCallback(waitObject):
		if not windll.kernel32.UnregisterWait(waitObject):
			if GetLastError() != ERROR_IO_PENDING:
				raise WinError()

	def waitForSingleObjectWithCallback(
		self,
		objectHandle: HANDLE | int,
		func: WaitOrTimerCallback,
		param=0,
		flags=WT_EXECUTELONGFUNCTION | WT_EXECUTEONLYONCE,
		waitTime=winKernel.INFINITE,
	):
		"""
		Registers a wait operation for a single object with a callback function to be executed
		when the wait is signaled or times out.

		Args:
			objectHandle: The handle to the object to wait on.
			func: The callback function to execute when the wait is signaled
				or times out. This can be a bound method or a callable object.
			param: A parameter to pass to the callback function. Defaults to 0.
			flags: Flags that control the behavior of the wait operation. Defaults
				to WT_EXECUTELONGFUNCTION | WT_EXECUTEONLYONCE.
			waitTime: The timeout interval, in milliseconds. Defaults to
				winKernel.INFINITE.

		Raises:
			RuntimeError: If the thread is not running.
			WinError: If the registration of the wait operation fails.

		Notes:
			- The callback function is stored as a weak reference to avoid circular references.
			- The wait operation is registered using the Windows API function
				`RegisterWaitForSingleObject`.
			- The `_waitOrTimerCallbackStore` dictionary is used to manage the state of the wait
				operation and its associated callback.

		"""

		if not self.is_alive():
			raise RuntimeError("Thread is not running")

		waitObject = HANDLE()
		reference = BoundMethodWeakref(func) if ismethod(func) else AnnotatableWeakref(func)
		reference.funcName = repr(func)
		waitObjectAddr = addressof(waitObject)
		self._waitOrTimerCallbackStore[waitObjectAddr] = (
			self.ident,
			waitObject,
			reference,
			param,
		)
		try:
			waitRes = windll.kernel32.RegisterWaitForSingleObject(
				byref(waitObject),
				objectHandle,
				self._internalWaitOrTimerCallback,
				waitObjectAddr,
				waitTime,
				flags,
			)
			if not waitRes:
				raise WinError()
		except Exception:
			del self._waitOrTimerCallbackStore[waitObjectAddr]
			raise
