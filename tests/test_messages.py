# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for outgoing message construction in RemoteProtocolHandler."""

from __future__ import annotations

import sys
import unittest

from lib import protocol

import tests  # noqa: F401 — bootstrap sys.path + stubs
from tests._fakes import FakeHandlerBase, buildMessage

# ---------------------------------------------------------------------------
# Helper subclasses
# ---------------------------------------------------------------------------


class _HandlerWithLanguageReceiver(FakeHandlerBase):
	"""Adds a LANGUAGE attributeReceiver so attribute receipt can be tested."""

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, payload: bytes) -> str:
		return payload.decode()


class _HandlerWithRecordingCommandHandler(FakeHandlerBase):
	"""Adds a SPEAK commandHandler that records the payload it receives."""

	def __init__(self):
		super().__init__()
		self.receivedPayloads: list[bytes] = []

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _handle_speak(self, payload: bytes):
		self.receivedPayloads.append(payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWriteMessage(unittest.TestCase):
	"""Test 1 & 2: basic writeMessage behaviour."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_write_message_speak_with_payload(self):
		"""writeMessage produces the correct wire bytes for a non-empty payload."""
		payload = b"abc"
		self.handler.writeMessage(protocol.SpeechCommand.SPEAK, payload)

		expected = b"S" + bytes([protocol.SpeechCommand.SPEAK]) + (3).to_bytes(2, sys.byteorder) + b"abc"
		self.assertEqual(self.handler._dev.writes, [expected])

	def test_write_message_matches_build_message(self):
		"""writeMessage output is identical to buildMessage helper."""
		payload = b"abc"
		self.handler.writeMessage(protocol.SpeechCommand.SPEAK, payload)

		expected = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.SpeechCommand.SPEAK,
			payload,
		)
		self.assertEqual(self.handler._dev.writes[0], expected)

	def test_write_message_default_empty_payload(self):
		"""writeMessage with no payload argument writes a zero-length field and no payload bytes."""
		self.handler.writeMessage(protocol.SpeechCommand.CANCEL)

		written = self.handler._dev.writes[0]
		# Length field is bytes 2-3; must be zero
		length_field = int.from_bytes(written[2:4], sys.byteorder)
		self.assertEqual(length_field, 0)
		# Total message size is exactly 4 bytes (header only)
		self.assertEqual(len(written), 4)


class TestLargePayloadRoundtrip(unittest.TestCase):
	"""Test 3: large payloads encode/decode correctly through _onReceive."""

	def setUp(self):
		self.sender = FakeHandlerBase()
		self.receiver = _HandlerWithRecordingCommandHandler()
		self.addCleanup(self.sender.terminate)
		self.addCleanup(self.receiver.terminate)

	def test_large_payload_length_field(self):
		"""300-byte payload encodes its length correctly in the 2-byte field."""
		payload = bytes(range(256)) + bytes(range(44))  # 300 bytes
		self.sender.writeMessage(protocol.SpeechCommand.SPEAK, payload)

		written = self.sender._dev.writes[0]
		length_field = int.from_bytes(written[2:4], sys.byteorder)
		self.assertEqual(length_field, 300)

	def test_large_payload_roundtrip_via_on_receive(self):
		"""Feeding large written bytes into _onReceive dispatches the payload intact."""
		payload = bytes(range(256)) + bytes(range(44))  # 300 bytes
		self.sender.writeMessage(protocol.SpeechCommand.SPEAK, payload)

		wire_bytes = self.sender._dev.writes[0]
		self.receiver._onReceive(wire_bytes)

		self.assertEqual(len(self.receiver.receivedPayloads), 1)
		self.assertEqual(self.receiver.receivedPayloads[0], payload)


class TestSetRemoteAttribute(unittest.TestCase):
	"""Test 4: setRemoteAttribute wire format."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_set_remote_attribute_payload_format(self):
		"""setRemoteAttribute writes ATTRIBUTE command with `attribute`value payload."""
		self.handler.setRemoteAttribute(b"language", b"nl")

		self.assertEqual(len(self.handler._dev.writes), 1)
		written = self.handler._dev.writes[0]

		# driverType byte
		self.assertEqual(written[0:1], b"S")
		# command byte
		self.assertEqual(written[1], protocol.GenericCommand.ATTRIBUTE)

		# payload is everything after the 4-byte header
		payload = written[4:]
		expected_payload = b"`language`nl"
		self.assertEqual(payload, expected_payload)


class TestRequestRemoteAttribute(unittest.TestCase):
	"""Tests 5 & 6: requestRemoteAttribute wire format and duplicate suppression."""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def test_request_remote_attribute_payload_format(self):
		"""requestRemoteAttribute writes ATTRIBUTE command with trailing separator and empty value."""
		self.handler.requestRemoteAttribute(b"language")

		self.assertEqual(len(self.handler._dev.writes), 1)
		written = self.handler._dev.writes[0]

		self.assertEqual(written[0:1], b"S")
		self.assertEqual(written[1], protocol.GenericCommand.ATTRIBUTE)

		payload = written[4:]
		# Empty value: `language` followed by separator and nothing
		expected_payload = b"`language`"
		self.assertEqual(payload, expected_payload)

	def test_request_remote_attribute_sets_pending(self):
		"""requestRemoteAttribute marks the attribute request as pending."""
		self.handler.requestRemoteAttribute(b"language")

		self.assertTrue(
			self.handler._attributeValueProcessor.isAttributeRequestPending(b"language"),
		)

	def test_duplicate_request_suppressed(self):
		"""Second requestRemoteAttribute for the same pending attribute does not write again."""
		self.handler.requestRemoteAttribute(b"language")
		writes_after_first = len(self.handler._dev.writes)

		self.handler.requestRemoteAttribute(b"language")
		writes_after_second = len(self.handler._dev.writes)

		self.assertEqual(writes_after_first, writes_after_second)


class TestPendingClearedOnReceipt(unittest.TestCase):
	"""Test 7: pending flag clears and value is stored when attribute value arrives."""

	def setUp(self):
		self.handler = _HandlerWithLanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_pending_cleared_after_value_received(self):
		"""isAttributeRequestPending returns False after the attribute value is processed."""
		attr = protocol.SpeechAttribute.LANGUAGE
		self.handler.requestRemoteAttribute(attr)
		self.assertTrue(self.handler._attributeValueProcessor.isAttributeRequestPending(attr))

		self.handler._attributeValueProcessor(attr, b"nl")

		self.assertFalse(self.handler._attributeValueProcessor.isAttributeRequestPending(attr))

	def test_value_stored_after_receipt(self):
		"""getValue returns the parsed value after the attribute has been pushed."""
		attr = protocol.SpeechAttribute.LANGUAGE
		self.handler.requestRemoteAttribute(attr)

		self.handler._attributeValueProcessor(attr, b"nl")

		value = self.handler._attributeValueProcessor.getValue(attr, fallBackToDefault=False)
		self.assertEqual(value, "nl")

	def test_pending_cleared_and_value_stored_without_prior_request(self):
		"""Attribute receipt without a prior request still stores the value and leaves pending=False."""
		attr = protocol.SpeechAttribute.LANGUAGE
		# No requestRemoteAttribute call — just a push from the remote side
		self.handler._attributeValueProcessor(attr, b"en-GB")

		self.assertFalse(self.handler._attributeValueProcessor.isAttributeRequestPending(attr))
		value = self.handler._attributeValueProcessor.getValue(attr, fallBackToDefault=False)
		self.assertEqual(value, "en-GB")


if __name__ == "__main__":
	unittest.main()
