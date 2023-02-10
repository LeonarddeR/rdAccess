from hwIo import IoThread, IoBase
import queueHandler
from threading import get_ident


class IoBaseThreadMixin(IoBase):
	_ioThread: IoThread
	_ioThreadStopped: bool = False

	def __init__(self, *args, **kwargs):
		self._ioThread = IoThread()
		self._ioThread.start()
		super().__init__(*args, **kwargs)

	def _initialRead(self):
		self._ioThread.queueAsApc(lambda param: self._asyncRead())

	def close(self):
		super().close()
		if not self._ioThreadStopped:
			if get_ident() == self._ioThread.ident:
				queueHandler.queueFunction(queueHandler.eventQueue, self._ioThread.stop)
			else:
				self._ioThread.stop()
			self._ioThreadStopped = True
