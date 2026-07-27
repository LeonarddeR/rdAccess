# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Test doubles for exercising ``lib.protocol`` without NVDA or a real pipe."""

from __future__ import annotations

import sys
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


class FakeHandlerBase(protocol.RemoteProtocolHandler):
	"""Concrete RemoteProtocolHandler attached to a FakeIo device."""

	driverType = protocol.DriverType.SPEECH

	def __init__(self):
		super().__init__()
		self._dev = FakeIo()

	def _onReadError(self, error: int) -> bool:
		return False

	def _incoming_setting(self, attribute: protocol.AttributeT, value: Any):
		raise NotImplementedError


def buildMessage(driverType: int, command: int, payload: bytes = b"") -> bytes:
	"""Construct a wire message as the remote end would send it."""
	return bytes((
		driverType,
		command,
		*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
		*payload,
	))


def speakFrame(sequence: list) -> bytes:
	"""Legacy SPEAK frame as a v1 speech peer would send it."""
	command, payload = protocol.legacy.encodeCommandPayload(
		protocol.DriverType.SPEECH,
		protocol.RdMessageType.SPEAK,
		{"sequence": sequence},
	)
	return buildMessage(protocol.DriverType.SPEECH, command, payload)
