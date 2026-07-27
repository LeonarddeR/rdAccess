# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for synchronous message dispatch in RemoteProtocolHandler.

Incoming messages and attribute update callbacks are handled inline on the
receiving thread, and a handler that raises does not affect later messages.
"""

from __future__ import annotations

import threading
import unittest
from typing import Any

from lib import protocol
from lib.protocol.messages import RdMessageType

from tests._fakes import FakeIo, buildMessage, speakFrame

DISPATCH_TIMEOUT = 2.0

PROBE_ATTRIBUTE = "test_dispatchProbe"


class _RawDispatchRecorder(protocol.RemoteProtocolHandler):
	"""Records the thread that runs command handlers and attribute update callbacks."""

	driverType = protocol.DriverType.SPEECH

	def __init__(self):
		super().__init__()
		self._dev = FakeIo()
		self.speakThreads: list[int] = []
		self.speakHandled = threading.Event()
		self.callbackThreads: list[int] = []
		self.callbackRan = threading.Event()

	def _onReadError(self, error: int) -> bool:
		return False

	def _incoming_setting(self, attribute: protocol.AttributeT, value: Any):
		raise NotImplementedError

	@protocol.commandHandler(RdMessageType.SPEAK)
	def _command_speak(self, sequence: list):
		self.speakThreads.append(threading.get_ident())
		self.speakHandled.set()

	@protocol.commandHandler(RdMessageType.CANCEL)
	def _command_cancel(self):
		raise RuntimeError("intentional handler failure")

	_incoming_probe = protocol.AttributeReceiver(PROBE_ATTRIBUTE, defaultValue=0)

	@_incoming_probe.updateCallback
	def _post_probe(self, attribute: protocol.AttributeT, value: int):
		self.callbackThreads.append(threading.get_ident())
		self.callbackRan.set()


class InlineDispatchTests(unittest.TestCase):
	def setUp(self):
		self.handler = _RawDispatchRecorder()
		self.addCleanup(self.handler.terminate)

	def _assertHandledOnCallingThread(self, handled: threading.Event, threads: list[int]):
		self.assertTrue(handled.wait(DISPATCH_TIMEOUT), "handler was never invoked")
		self.assertEqual(threads, [threading.get_ident()])

	def test_jsonMessageIsHandledOnTheReceivingThread(self):
		self.handler._onReceive(b'{"type": "speak", "sequence": ["hello"]}\n')
		self._assertHandledOnCallingThread(self.handler.speakHandled, self.handler.speakThreads)

	def test_legacyFrameIsHandledOnTheReceivingThread(self):
		self.handler._onReceive(speakFrame(["hello"]))
		self._assertHandledOnCallingThread(self.handler.speakHandled, self.handler.speakThreads)

	def test_attributeUpdateCallbackRunsOnTheSettingThread(self):
		self.handler._attributeValueProcessor(PROBE_ATTRIBUTE, 42)
		self._assertHandledOnCallingThread(self.handler.callbackRan, self.handler.callbackThreads)

	def test_jsonHandlerErrorDoesNotDropSubsequentMessages(self):
		chunk = b'{"type": "cancel"}\n{"type": "speak", "sequence": ["after error"]}\n'
		self.handler._onReceive(chunk)
		self.assertEqual(len(self.handler.speakThreads), 1)

	def test_legacyHandlerErrorDoesNotDropSubsequentFrames(self):
		command, payload = protocol.legacy.encodeCommandPayload(
			protocol.DriverType.SPEECH,
			RdMessageType.CANCEL,
			{},
		)
		chunk = buildMessage(protocol.DriverType.SPEECH, command, payload) + speakFrame(["after error"])
		self.handler._onReceive(chunk)
		self.assertEqual(len(self.handler.speakThreads), 1)


if __name__ == "__main__":
	unittest.main()
