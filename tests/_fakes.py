# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Test doubles for exercising ``lib.protocol`` without NVDA or a real pipe."""

from __future__ import annotations

import sys
from concurrent.futures import Future
from typing import Any

from hwIo.base import IoBase
from lib import protocol


class FakeIo(IoBase):
	"""Captures written messages and serves scripted waitForRead results."""

	def __init__(self):
		self.writes: list[bytes] = []
		self.waitForReadResults: list[bool] = []
		self.closed = False

	def write(self, data: bytes):
		self.writes.append(data)

	def waitForRead(self, timeout: float) -> bool:
		if self.waitForReadResults:
			return self.waitForReadResults.pop(0)
		return False

	def close(self):
		self.closed = True


class InlineExecutor:
	"""Drop-in for the handler's ThreadPoolExecutor that runs submissions synchronously.

	Exceptions are captured on the returned future, mirroring how a real executor
	swallows them when the future is discarded.
	"""

	def __init__(self):
		self.isShutdown = False

	def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future:
		future: Future = Future()
		try:
			future.set_result(fn(*args, **kwargs))
		except BaseException as e:  # noqa: BLE001
			future.set_exception(e)
		return future

	def shutdown(self, wait: bool = True, *, cancel_futures: bool = False):
		self.isShutdown = True


class FakeHandlerBase(protocol.RemoteProtocolHandler):
	"""Concrete RemoteProtocolHandler attached to a FakeIo device.

	Background execution is synchronous (InlineExecutor), so command dispatch and
	attribute processing triggered through _onReceive complete before it returns.
	"""

	driverType = protocol.DriverType.SPEECH

	def __init__(self):
		super().__init__()
		self._bgExecutor.shutdown(wait=False)
		self._bgExecutor = InlineExecutor()
		self._dev = FakeIo()

	def _onReadError(self, error: int) -> bool:
		return False

	def _incoming_setting(self, attribute: protocol.AttributeT, payLoad: bytes):
		raise NotImplementedError


def buildMessage(driverType: int, command: int, payload: bytes = b"") -> bytes:
	"""Construct a wire message as the remote end would send it."""
	return bytes((
		driverType,
		command,
		*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
		*payload,
	))
