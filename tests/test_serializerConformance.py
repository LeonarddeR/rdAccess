# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Conformance tests against NVDA core's Remote Access protocol.

These tests compare RDAccess's protocol v2 with the ``_remoteClient`` modules from the
sibling NVDA source checkout. They fail as soon as the NVDA Remote wire protocol drifts
from what RDAccess mirrors.
"""

from __future__ import annotations

import unittest

import speech.commands
from lib.protocol import serializer as rdSerializer
from lib.protocol.messages import RdMessageType

from ._nvdaRemote import protocol as nvdaRemoteProtocol, serializer as nvdaRemoteSerializer


class MessageTypeConformanceTests(unittest.TestCase):
	"""Mirrored message type values must stay identical to RemoteMessageType."""

	MIRRORED_MEMBERS = (
		"PROTOCOL_VERSION",
		"PING",
		"SPEAK",
		"CANCEL",
		"PAUSE_SPEECH",
		"TONE",
		"WAVE",
		"INDEX",
		"DISPLAY",
		"BRAILLE_INPUT",
	)

	def test_mirroredValuesMatchNvdaRemote(self):
		for name in self.MIRRORED_MEMBERS:
			with self.subTest(member=name):
				self.assertEqual(
					RdMessageType[name].value,
					nvdaRemoteProtocol.RemoteMessageType[name].value,
				)

	def test_rdAccessSpecificMembersAbsentFromNvdaRemote(self):
		"""RDAccess-specific types must not collide with names NVDA Remote may assign later
		to different semantics without conformance tests noticing."""
		rdSpecific = set(RdMessageType.__members__) - set(self.MIRRORED_MEMBERS)
		for name in rdSpecific:
			with self.subTest(member=name):
				self.assertNotIn(name, nvdaRemoteProtocol.RemoteMessageType.__members__)


class SerializerConformanceTests(unittest.TestCase):
	"""Shared message types must serialize byte-for-byte identically to NVDA Remote."""

	def setUp(self):
		self.ours = rdSerializer.RdJSONSerializer()
		self.theirs = nvdaRemoteSerializer.JSONSerializer()

	def test_separator(self):
		self.assertEqual(rdSerializer.RdJSONSerializer.SEP, nvdaRemoteSerializer.JSONSerializer.SEP)

	def test_sequenceClasses(self):
		self.assertEqual(rdSerializer.SEQUENCE_CLASSES, nvdaRemoteSerializer.SEQUENCE_CLASSES)

	def _sampleSequence(self) -> list:
		return [
			"Hello ",
			speech.commands.IndexCommand(1),
			"world",
			speech.commands.PitchCommand(offset=30),
			speech.commands.BreakCommand(time=50),
			speech.commands.EndUtteranceCommand(),
		]

	def test_serializeByteEquality(self):
		cases = (
			("speak", {"sequence": self._sampleSequence()}),
			("cancel", {}),
			("pause_speech", {"switch": True}),
			("tone", {"hz": 440.0, "length": 100, "left": 50, "right": 50}),
			("wave", {"fileName": "waves/browseMode.wav"}),
			("index", {"index": 5}),
			("display", {"cells": [0, 1, 255]}),
			("protocol_version", {"version": 2}),
			("ping", {}),
		)
		for msgType, payload in cases:
			with self.subTest(type=msgType):
				self.assertEqual(
					self.ours.serialize(type=RdMessageType(msgType), **payload),
					self.theirs.serialize(
						type=nvdaRemoteProtocol.RemoteMessageType(msgType),
						**payload,
					),
				)

	def test_crossDeserializeSpeak(self):
		sequence = self._sampleSequence()
		fromTheirs = self.ours.deserialize(self.theirs.serialize(type="speak", sequence=sequence))
		self.assertEqual(fromTheirs["sequence"], sequence)
		fromOurs = self.theirs.deserialize(self.ours.serialize(type="speak", sequence=sequence))
		self.assertEqual(fromOurs["sequence"], sequence)
