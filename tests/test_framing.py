# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for RemoteProtocolHandler wire-framing (_onReceive / writeMessage)."""

from __future__ import annotations

import contextlib
import unittest

from lib import protocol

from tests._fakes import FakeHandlerBase, buildMessage

# ---------------------------------------------------------------------------
# Concrete handler used by all framing tests.
# ---------------------------------------------------------------------------


class SpeakCapture(FakeHandlerBase):
	"""Records payloads delivered to the SPEAK command handler."""

	def __init__(self):
		# Initialise the capture list before super().__init__ so it is available
		# immediately after construction (super().__init__ is safe here — __new__
		# has already done all decorator registration).
		self.speak_payloads: list[bytes] = []
		super().__init__()

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _on_speak(self, payload: bytes) -> None:
		self.speak_payloads.append(payload)


# ---------------------------------------------------------------------------
# 1. Complete message → handler invoked once with exact payload.
# ---------------------------------------------------------------------------


class TestCompleteMessage(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_single_complete_message_dispatches_once(self):
		payload = b"hello world"
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads, [payload])

	def test_single_complete_message_exact_payload_content(self):
		payload = b"\x00\x01\x02\x03"
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload)
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler.speak_payloads), 1)
		self.assertEqual(self.handler.speak_payloads[0], payload)


# ---------------------------------------------------------------------------
# 2. Partial delivery (split AFTER the 4-byte header).
# ---------------------------------------------------------------------------


class TestPartialDelivery(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_two_way_split_after_header(self):
		"""header + first half of payload → no dispatch; second half → dispatch once."""
		payload = b"abcdefghij"  # 10 bytes
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload)
		# Split at byte 4+5 = 9 (header is 4 bytes, split in the middle of payload)
		split = 4 + 5
		self.handler._onReceive(msg[:split])
		self.assertEqual(
			self.handler.speak_payloads,
			[],
			"No dispatch expected before full payload arrives",
		)
		self.handler._onReceive(msg[split:])
		self.assertEqual(self.handler.speak_payloads, [payload])

	def test_three_way_split(self):
		"""Three chunks spanning the payload → exactly one dispatch with full payload."""
		payload = b"0123456789abcdef"  # 16 bytes
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload)
		# All split points are strictly after the 4-byte header.
		split1 = 4 + 4  # header + first 4 bytes of payload
		split2 = 4 + 10  # header + first 10 bytes of payload
		self.handler._onReceive(msg[:split1])
		self.assertEqual(self.handler.speak_payloads, [])
		self.handler._onReceive(msg[split1:split2])
		self.assertEqual(self.handler.speak_payloads, [])
		self.handler._onReceive(msg[split2:])
		self.assertEqual(self.handler.speak_payloads, [payload])

	def test_split_one_byte_before_end(self):
		"""All but the last payload byte in the first chunk."""
		payload = b"xyz"
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload)
		split = len(msg) - 1
		self.handler._onReceive(msg[:split])
		self.assertEqual(self.handler.speak_payloads, [])
		self.handler._onReceive(msg[split:])
		self.assertEqual(self.handler.speak_payloads, [payload])


# ---------------------------------------------------------------------------
# 3. Coalesced messages: two complete messages in one _onReceive call.
# ---------------------------------------------------------------------------


class TestCoalescedMessages(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_two_complete_messages_both_dispatched(self):
		payload1 = b"first"
		payload2 = b"second"
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload1) + buildMessage(
			protocol.DriverType.SPEECH,
			protocol.SpeechCommand.SPEAK,
			payload2,
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads, [payload1, payload2])

	def test_three_complete_messages_all_dispatched_in_order(self):
		payloads = [b"alpha", b"beta", b"gamma"]
		msg = b"".join(
			buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, p) for p in payloads
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads, payloads)

	def test_coalesced_preserves_payload_content(self):
		payload1 = b"\xff\xfe"
		payload2 = b"\x00"
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload1) + buildMessage(
			protocol.DriverType.SPEECH,
			protocol.SpeechCommand.SPEAK,
			payload2,
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads[0], payload1)
		self.assertEqual(self.handler.speak_payloads[1], payload2)


# ---------------------------------------------------------------------------
# 4. Coalesced partial: message1 complete + first half of message2 in one call,
#    rest of message2 in second call.
# ---------------------------------------------------------------------------


class TestCoalescedPartial(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_complete_plus_partial_then_remainder(self):
		payload1 = b"complete"
		payload2 = b"partial-message-payload"
		msg1 = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload1)
		msg2 = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, payload2)
		# Split msg2 after its header, in the middle of its payload.
		split_in_msg2 = 4 + len(payload2) // 2
		first_chunk = msg1 + msg2[:split_in_msg2]
		second_chunk = msg2[split_in_msg2:]
		self.handler._onReceive(first_chunk)
		# message1 must have been dispatched; message2 not yet.
		self.assertEqual(self.handler.speak_payloads, [payload1])
		self.handler._onReceive(second_chunk)
		self.assertEqual(self.handler.speak_payloads, [payload1, payload2])

	def test_two_complete_then_partial_then_rest(self):
		"""Two complete messages, then a partial, then the rest of the partial."""
		payloads = [b"one", b"two", b"three-is-the-long-one"]
		msgs = [buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, p) for p in payloads]
		# First call: msgs[0] + msgs[1] + first half of msgs[2]
		split = 4 + len(payloads[2]) // 2
		first_chunk = msgs[0] + msgs[1] + msgs[2][:split]
		second_chunk = msgs[2][split:]
		self.handler._onReceive(first_chunk)
		self.assertEqual(self.handler.speak_payloads, [payloads[0], payloads[1]])
		self.handler._onReceive(second_chunk)
		self.assertEqual(self.handler.speak_payloads, payloads)


# ---------------------------------------------------------------------------
# 5. Wrong driverType → RuntimeError raised synchronously.
# ---------------------------------------------------------------------------


class TestWrongDriverType(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_braille_drivertype_on_speech_handler_raises(self):
		msg = buildMessage(protocol.DriverType.BRAILLE, protocol.SpeechCommand.SPEAK, b"data")
		with self.assertRaises(RuntimeError):
			self.handler._onReceive(msg)

	def test_wrong_drivertype_no_dispatch(self):
		"""Even though an error is raised, no SPEAK handler should have fired."""
		msg = buildMessage(protocol.DriverType.BRAILLE, protocol.SpeechCommand.SPEAK, b"data")
		with contextlib.suppress(RuntimeError):
			self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads, [])


# ---------------------------------------------------------------------------
# 6. Empty payload message dispatches with b"".
# ---------------------------------------------------------------------------


class TestEmptyPayload(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_empty_payload_dispatches(self):
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"")
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler.speak_payloads), 1)

	def test_empty_payload_value_is_empty_bytes(self):
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"")
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_payloads[0], b"")

	def test_empty_payload_then_nonempty(self):
		"""Empty-payload message followed by a message with payload — both dispatched."""
		msg1 = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"")
		msg2 = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"after")
		self.handler._onReceive(msg1 + msg2)
		self.assertEqual(self.handler.speak_payloads, [b"", b"after"])


if __name__ == "__main__":
	unittest.main()
