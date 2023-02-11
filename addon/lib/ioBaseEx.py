from __future__ import annotations
from hwIo import IoThread, IoBase
import weakref
from typing import Callable, Optional, Union
import ctypes
import ctypes.wintypes


class IoBaseEx(IoBase):
	_ioThreadRef: weakref.ReferenceType[IoThread]

	def __init__(
			self,
			fileHandle: Union[ctypes.wintypes.HANDLE, int],
			onReceive: Callable[[bytes], None],
			writeFileHandle: Optional[ctypes.wintypes.HANDLE] = None,
			onReceiveSize: int = 1,
			onReadError: Optional[Callable[[int], bool]] = None,
			ioThread: Optional[IoThread] = None
	):
		if ioThread is None:
			from hwIo import bgThread as ioThread
		self._ioThreadRef = weakref.ref(ioThread)
		super().__init__(fileHandle, onReceive, writeFileHandle, onReceiveSize, onReadError)

	def _initialRead(self):
		ioThread = self._ioThreadRef()
		if not ioThread:
			raise RuntimeError("I/O thread is no longer available")
		ioThread.queueAsApc(lambda param: self._asyncRead())
