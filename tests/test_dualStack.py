# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Tests for the dual-stack send-path switch and protocol version handshake.

Two in-process handlers are wired write-to-receive to simulate a connection.
The InlineExecutor in FakeHandlerBase makes all dispatch synchronous, so a
"pump" that forwards captured writes drains the conversation deterministically.
"""

from __future__ import annotations

import unittest

from lib import protocol
from lib.protocol import legacy
from lib.protocol.messages import CHANNEL_NAMES, PROTOCOL_VERSION, RdMessageType

from tests._fakes import FakeHandlerBase, buildMessage


def _versionPushFrame(version: int) -> bytes:
	"""Legacy-format protocolVersion attribute push, as a v2 peer sends it at connect."""
	command, payload = legacy.encodeCommandPayload(
		protocol.DriverType.SPEECH,
		RdMessageType.ATTRIBUTE_VALUE,
		{"attribute": protocol.GenericAttribute.PROTOCOL_VERSION, "value": version},
	)
	return buildMessage(protocol.DriverType.SPEECH, command, payload)


class ConversingHandler(FakeHandlerBase):
	"""Speaks both directions: records SPEAK dispatches and serves LANGUAGE."""

	language = "nl"

	def __init__(self):
		self.speak_sequences: list[list] = []
		super().__init__()

	@protocol.commandHandler(RdMessageType.SPEAK)
	def _command_speak(self, sequence: list):
		self.speak_sequences.append(sequence)

	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self) -> str:
		return self.language

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, value: str) -> str:
		return value


class LegacyPinnedHandler(ConversingHandler):
	"""Simulates a protocol v1 peer: never pushes its version and never switches."""

	def _handlePeerProtocolVersionChange(self, version: int):
		pass

	def pushProtocolVersion(self):
		pass


def _pump(a: ConversingHandler, b: ConversingHandler, maxRounds: int = 10):
	"""Forward captured writes between both handlers until the conversation settles."""
	for _ in range(maxRounds):
		aOut = a._dev.writes[:]
		bOut = b._dev.writes[:]
		a._dev.writes.clear()
		b._dev.writes.clear()
		if not aOut and not bOut:
			return
		for data in aOut:
			b._onReceive(data)
		for data in bOut:
			a._onReceive(data)
	raise AssertionError("Conversation did not settle")


class TestSendPathSwitch(unittest.TestCase):
	def setUp(self):
		self.handler = ConversingHandler()
		self.addCleanup(self.handler.terminate)

	def test_initial_send_is_legacy(self):
		self.handler.sendMessage(RdMessageType.SPEAK, sequence=["hi"])
		self.assertEqual(self.handler._dev.writes[0][0], protocol.DriverType.SPEECH)

	def test_legacy_version_push_switches_to_json(self):
		self.handler._onReceive(_versionPushFrame(2))
		self.assertTrue(self.handler._sendJson)
		self.handler._dev.writes.clear()
		self.handler.sendMessage(RdMessageType.SPEAK, sequence=["hi"])
		self.assertEqual(self.handler._dev.writes[0][0:1], b"{")

	def test_switch_emits_one_shot_json_handshake(self):
		self.handler._onReceive(_versionPushFrame(2))
		jsonWrites = [w for w in self.handler._dev.writes if w.startswith(b"{")]
		self.assertEqual(len(jsonWrites), 1)
		obj = self.handler._serializer.deserialize(jsonWrites[0])
		self.assertEqual(obj["type"], RdMessageType.PROTOCOL_VERSION.value)
		self.assertEqual(obj["version"], PROTOCOL_VERSION)
		self.assertEqual(obj["channel"], CHANNEL_NAMES[protocol.DriverType.SPEECH])

	def test_handshake_not_repeated(self):
		self.handler._onReceive(_versionPushFrame(2))
		self.handler._dev.writes.clear()
		self.handler._onReceive(_versionPushFrame(2))
		self.assertEqual(self.handler._dev.writes, [])

	def test_incoming_json_line_switches_implicitly(self):
		line = self.handler._serializer.serialize(type=RdMessageType.SPEAK, sequence=["x"])
		self.handler._onReceive(line)
		self.assertTrue(self.handler._sendJson)

	def test_version_1_push_does_not_switch(self):
		self.handler._onReceive(_versionPushFrame(1))
		self.assertFalse(self.handler._sendJson)
		self.handler._dev.writes.clear()
		self.handler.sendMessage(RdMessageType.CANCEL)
		self.assertEqual(self.handler._dev.writes[0][0], protocol.DriverType.SPEECH)

	def test_push_protocol_version_uses_legacy_format(self):
		self.handler.pushProtocolVersion()
		written = self.handler._dev.writes[0]
		self.assertEqual(written[0], protocol.DriverType.SPEECH)
		self.assertEqual(written[1], protocol.GenericCommand.ATTRIBUTE)
		self.assertIn(b"`protocolVersion`", written)


class TestPeerInterop(unittest.TestCase):
	def _connect(self, a: ConversingHandler, b: ConversingHandler):
		a.pushProtocolVersion()
		b.pushProtocolVersion()
		_pump(a, b)

	def test_two_v2_peers_migrate_to_json(self):
		a = ConversingHandler()
		self.addCleanup(a.terminate)
		b = ConversingHandler()
		self.addCleanup(b.terminate)
		self._connect(a, b)
		self.assertTrue(a._sendJson)
		self.assertTrue(b._sendJson)

		a.sendMessage(RdMessageType.SPEAK, sequence=["json speech"])
		self.assertEqual(a._dev.writes[0][0:1], b"{")
		_pump(a, b)
		self.assertEqual(b.speak_sequences, [["json speech"]])

	def test_two_v2_peers_attribute_roundtrip_in_json_mode(self):
		a = ConversingHandler()
		self.addCleanup(a.terminate)
		b = ConversingHandler()
		self.addCleanup(b.terminate)
		b.language = "de"
		self._connect(a, b)

		a.requestRemoteAttribute(protocol.SpeechAttribute.LANGUAGE)
		_pump(a, b)
		value = a._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=False,
		)
		self.assertEqual(value, "de")

	def test_v2_peer_with_v1_peer_stays_legacy(self):
		new = ConversingHandler()
		self.addCleanup(new.terminate)
		old = LegacyPinnedHandler()
		self.addCleanup(old.terminate)
		self._connect(new, old)
		self.assertFalse(new._sendJson)
		self.assertFalse(old._sendJson)

		new.sendMessage(RdMessageType.SPEAK, sequence=["legacy speech"])
		self.assertEqual(new._dev.writes[0][0], protocol.DriverType.SPEECH)
		_pump(new, old)
		self.assertEqual(old.speak_sequences, [["legacy speech"]])

	def test_v1_peer_speech_reaches_v2_peer(self):
		new = ConversingHandler()
		self.addCleanup(new.terminate)
		old = LegacyPinnedHandler()
		self.addCleanup(old.terminate)
		self._connect(new, old)

		old.sendMessage(RdMessageType.SPEAK, sequence=["old to new"])
		_pump(new, old)
		self.assertEqual(new.speak_sequences, [["old to new"]])

	def test_attribute_roundtrip_with_v1_peer(self):
		new = ConversingHandler()
		self.addCleanup(new.terminate)
		old = LegacyPinnedHandler()
		self.addCleanup(old.terminate)
		old.language = "fr"
		self._connect(new, old)

		new.requestRemoteAttribute(protocol.SpeechAttribute.LANGUAGE)
		_pump(new, old)
		value = new._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=False,
		)
		self.assertEqual(value, "fr")


if __name__ == "__main__":
	unittest.main()
