# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for RemoteProtocolHandler wire-framing (_onReceive / writeMessage)."""

from __future__ import annotations

import contextlib
import unittest

from lib import protocol
from lib.protocol import legacy
from lib.protocol.messages import RdMessageType

from tests._fakes import FakeHandlerBase, buildMessage

# ---------------------------------------------------------------------------
# Concrete handler used by all framing tests.
# ---------------------------------------------------------------------------


class SpeakCapture(FakeHandlerBase):
	"""Records sequences delivered to the SPEAK command handler."""

	def __init__(self):
		# Initialise the capture list before super().__init__ so it is available
		# immediately after construction (super().__init__ is safe here — __new__
		# has already done all decorator registration).
		self.speak_sequences: list[list] = []
		self.cancel_calls: int = 0
		super().__init__()

	@protocol.commandHandler(RdMessageType.SPEAK)
	def _on_speak(self, sequence: list) -> None:
		self.speak_sequences.append(sequence)

	@protocol.commandHandler(RdMessageType.CANCEL)
	def _on_cancel(self) -> None:
		self.cancel_calls += 1


def _speakFrame(sequence: list) -> bytes:
	command, payload = legacy.encodeCommandPayload(
		protocol.DriverType.SPEECH,
		RdMessageType.SPEAK,
		{"sequence": sequence},
	)
	return buildMessage(protocol.DriverType.SPEECH, command, payload)


# ---------------------------------------------------------------------------
# 1. Complete message → handler invoked once with exact payload.
# ---------------------------------------------------------------------------


class TestCompleteMessage(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_single_complete_message_dispatches_once(self):
		sequence = ["hello world"]
		self.handler._onReceive(_speakFrame(sequence))
		self.assertEqual(self.handler.speak_sequences, [sequence])

	def test_single_complete_message_exact_payload_content(self):
		sequence = ["\x00\x01\x02\x03", "second item"]
		self.handler._onReceive(_speakFrame(sequence))
		self.assertEqual(len(self.handler.speak_sequences), 1)
		self.assertEqual(self.handler.speak_sequences[0], sequence)


# ---------------------------------------------------------------------------
# 2. Partial delivery (split AFTER the 4-byte header).
# ---------------------------------------------------------------------------


class TestPartialDelivery(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_two_way_split_after_header(self):
		"""header + first half of payload → no dispatch; second half → dispatch once."""
		sequence = ["abcdefghij"]
		msg = _speakFrame(sequence)
		# Split at byte 9 (header is 4 bytes, split in the middle of payload)
		split = 4 + 5
		self.handler._onReceive(msg[:split])
		self.assertEqual(
			self.handler.speak_sequences,
			[],
			"No dispatch expected before full payload arrives",
		)
		self.handler._onReceive(msg[split:])
		self.assertEqual(self.handler.speak_sequences, [sequence])

	def test_three_way_split(self):
		"""Three chunks spanning the payload → exactly one dispatch with full payload."""
		sequence = ["0123456789abcdef"]
		msg = _speakFrame(sequence)
		# All split points are strictly after the 4-byte header.
		split1 = 4 + 4
		split2 = 4 + 10
		self.handler._onReceive(msg[:split1])
		self.assertEqual(self.handler.speak_sequences, [])
		self.handler._onReceive(msg[split1:split2])
		self.assertEqual(self.handler.speak_sequences, [])
		self.handler._onReceive(msg[split2:])
		self.assertEqual(self.handler.speak_sequences, [sequence])

	def test_split_one_byte_before_end(self):
		"""All but the last payload byte in the first chunk."""
		sequence = ["xyz"]
		msg = _speakFrame(sequence)
		split = len(msg) - 1
		self.handler._onReceive(msg[:split])
		self.assertEqual(self.handler.speak_sequences, [])
		self.handler._onReceive(msg[split:])
		self.assertEqual(self.handler.speak_sequences, [sequence])


# ---------------------------------------------------------------------------
# 3. Coalesced messages: two complete messages in one _onReceive call.
# ---------------------------------------------------------------------------


class TestCoalescedMessages(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_two_complete_messages_both_dispatched(self):
		sequence1 = ["first"]
		sequence2 = ["second"]
		self.handler._onReceive(_speakFrame(sequence1) + _speakFrame(sequence2))
		self.assertEqual(self.handler.speak_sequences, [sequence1, sequence2])

	def test_three_complete_messages_all_dispatched_in_order(self):
		sequences = [["alpha"], ["beta"], ["gamma"]]
		msg = b"".join(_speakFrame(s) for s in sequences)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_sequences, sequences)

	def test_coalesced_preserves_payload_content(self):
		sequence1 = ["\xff\xfe"]
		sequence2 = ["\x00"]
		self.handler._onReceive(_speakFrame(sequence1) + _speakFrame(sequence2))
		self.assertEqual(self.handler.speak_sequences[0], sequence1)
		self.assertEqual(self.handler.speak_sequences[1], sequence2)


# ---------------------------------------------------------------------------
# 4. Coalesced partial: message1 complete + first half of message2 in one call,
#    rest of message2 in second call.
# ---------------------------------------------------------------------------


class TestCoalescedPartial(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_complete_plus_partial_then_remainder(self):
		sequence1 = ["complete"]
		sequence2 = ["partial-message-payload"]
		msg1 = _speakFrame(sequence1)
		msg2 = _speakFrame(sequence2)
		# Split msg2 after its header, in the middle of its payload.
		split_in_msg2 = 4 + (len(msg2) - 4) // 2
		self.handler._onReceive(msg1 + msg2[:split_in_msg2])
		# message1 must have been dispatched; message2 not yet.
		self.assertEqual(self.handler.speak_sequences, [sequence1])
		self.handler._onReceive(msg2[split_in_msg2:])
		self.assertEqual(self.handler.speak_sequences, [sequence1, sequence2])

	def test_two_complete_then_partial_then_rest(self):
		"""Two complete messages, then a partial, then the rest of the partial."""
		sequences = [["one"], ["two"], ["three-is-the-long-one"]]
		msgs = [_speakFrame(s) for s in sequences]
		split = 4 + (len(msgs[2]) - 4) // 2
		self.handler._onReceive(msgs[0] + msgs[1] + msgs[2][:split])
		self.assertEqual(self.handler.speak_sequences, [sequences[0], sequences[1]])
		self.handler._onReceive(msgs[2][split:])
		self.assertEqual(self.handler.speak_sequences, sequences)


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
		self.assertEqual(self.handler.speak_sequences, [])


# ---------------------------------------------------------------------------
# 6. Empty payload message dispatches (CANCEL has an empty payload on the wire).
# ---------------------------------------------------------------------------


class TestEmptyPayload(unittest.TestCase):
	def setUp(self):
		self.handler = SpeakCapture()
		self.addCleanup(self.handler.terminate)

	def test_empty_payload_dispatches(self):
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.CANCEL, b"")
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.cancel_calls, 1)

	def test_empty_payload_then_nonempty(self):
		"""Empty-payload message followed by a message with payload — both dispatched."""
		msg1 = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.CANCEL, b"")
		msg2 = _speakFrame(["after"])
		self.handler._onReceive(msg1 + msg2)
		self.assertEqual(self.handler.cancel_calls, 1)
		self.assertEqual(self.handler.speak_sequences, [["after"]])


if __name__ == "__main__":
	unittest.main()
