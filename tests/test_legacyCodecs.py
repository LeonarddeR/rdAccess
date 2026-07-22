# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Tests for the legacy (protocol v1) byte codecs in ``lib.protocol.legacy``.

Encoded output is compared against golden bytes matching what protocol v1 peers
put on the wire, so the legacy path stays wire-compatible while the rest of the
handler moves to value-based messages.
"""

from __future__ import annotations

import pickle
import sys
import unittest
from unittest import mock

import speech.commands
from autoSettingsUtils.driverSetting import DriverSetting
from lib.protocol import legacy
from lib.protocol.braille import BrailleCommand, BrailleInputGesture
from lib.protocol.messages import RdMessageType
from lib.protocol.speech import SpeechCommand

from ._fakes import buildMessage


def _goldenPickle(obj) -> bytes:
	return pickle.dumps(obj, protocol=4)


class FrameTests(unittest.TestCase):
	def test_packFrameMatchesWireFormat(self):
		payload = b"payload bytes"
		self.assertEqual(
			legacy.packFrame(legacy.DriverType.SPEECH, SpeechCommand.SPEAK, payload),
			buildMessage(legacy.DriverType.SPEECH, SpeechCommand.SPEAK, payload),
		)


class PickleHelperTests(unittest.TestCase):
	"""Tests for legacy.dumps and legacy.loads."""

	def test_roundtrip_plain_structure(self):
		original = {"key": b"bytes_value", "name": "hello", "count": 42}
		self.assertEqual(legacy.loads(legacy.dumps(original)), original)

	def test_loads_calls_invalidate_cache_on_auto_property_object(self):
		"""loads calls invalidateCache on AutoPropertyObject results.

		DriverSetting is used as the probe (rather than an ad hoc AutoPropertyObject subclass)
		because RestrictedUnpickler only resolves allowlisted classes; see
		tests/test_restrictedUnpickling.py for the allowlist itself.
		"""
		raw = legacy.dumps(DriverSetting("id1", "Setting 1"))
		with mock.patch.object(DriverSetting, "invalidateCache") as invalidateCache:
			result = legacy.loads(raw)
		self.assertIsInstance(result, DriverSetting)
		invalidateCache.assert_called_once_with()

	def test_loads_does_not_call_invalidate_cache_on_plain_objects(self):
		"""loads does not call invalidateCache on non-AutoPropertyObject results."""
		# dict has no invalidateCache; if loads tried to call it this would raise.
		data = {"x": 1}
		self.assertEqual(legacy.loads(legacy.dumps(data)), data)


class SpeechCommandCodecTests(unittest.TestCase):
	def test_speak(self):
		sequence = ["Hello", speech.commands.IndexCommand(5)]
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.SPEECH,
			RdMessageType.SPEAK,
			{"sequence": sequence},
		)
		self.assertEqual(command, SpeechCommand.SPEAK)
		self.assertEqual(payload, _goldenPickle(sequence))
		msgType, kwargs = legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload)
		self.assertEqual(msgType, RdMessageType.SPEAK)
		self.assertEqual(kwargs, {"sequence": sequence})

	def test_cancel(self):
		command, payload = legacy.encodeCommandPayload(legacy.DriverType.SPEECH, RdMessageType.CANCEL, {})
		self.assertEqual(command, SpeechCommand.CANCEL)
		self.assertEqual(payload, b"")
		self.assertEqual(
			legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
			(RdMessageType.CANCEL, {}),
		)

	def test_pause(self):
		for switch, expected in ((True, b"\x01"), (False, b"\x00")):
			with self.subTest(switch=switch):
				command, payload = legacy.encodeCommandPayload(
					legacy.DriverType.SPEECH,
					RdMessageType.PAUSE_SPEECH,
					{"switch": switch},
				)
				self.assertEqual(command, SpeechCommand.PAUSE)
				self.assertEqual(payload, expected)
				self.assertEqual(
					legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
					(RdMessageType.PAUSE_SPEECH, {"switch": switch}),
				)

	def test_index(self):
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.SPEECH,
			RdMessageType.INDEX,
			{"index": 42},
		)
		self.assertEqual(command, SpeechCommand.INDEX_REACHED)
		self.assertEqual(payload, (42).to_bytes(2, sys.byteorder, signed=False))
		self.assertEqual(
			legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
			(RdMessageType.INDEX, {"index": 42}),
		)

	def test_toneAndWave(self):
		for msgType, command, kwargs in (
			(RdMessageType.TONE, SpeechCommand.BEEP, {"hz": 440.0, "length": 100, "left": 50, "right": 50}),
			(RdMessageType.WAVE, SpeechCommand.PLAY_WAVE_FILE, {"fileName": "waves/exit.wav"}),
		):
			with self.subTest(type=msgType):
				encodedCommand, payload = legacy.encodeCommandPayload(
					legacy.DriverType.SPEECH,
					msgType,
					dict(kwargs),
				)
				self.assertEqual(encodedCommand, command)
				self.assertEqual(payload, _goldenPickle(kwargs))
				self.assertEqual(
					legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
					(msgType, kwargs),
				)


class BrailleCommandCodecTests(unittest.TestCase):
	def test_display(self):
		cells = [0, 1, 128, 255]
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.BRAILLE,
			RdMessageType.DISPLAY,
			{"cells": cells},
		)
		self.assertEqual(command, BrailleCommand.DISPLAY)
		self.assertEqual(payload, bytes(cells))
		self.assertEqual(
			legacy.decodeCommandPayload(legacy.DriverType.BRAILLE, command, payload),
			(RdMessageType.DISPLAY, {"cells": cells}),
		)

	def test_brailleInput(self):
		kwargs = {
			"source": "remote",
			"id": "dot1",
			"routingIndex": None,
			"model": None,
			"dots": 1,
			"space": False,
		}
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.BRAILLE,
			RdMessageType.BRAILLE_INPUT,
			dict(kwargs),
		)
		self.assertEqual(command, BrailleCommand.EXECUTE_GESTURE)
		gesture = legacy.restrictedLoads(payload)
		self.assertIsInstance(gesture, BrailleInputGesture)
		msgType, decoded = legacy.decodeCommandPayload(legacy.DriverType.BRAILLE, command, payload)
		self.assertEqual(msgType, RdMessageType.BRAILLE_INPUT)
		self.assertEqual(decoded, kwargs)

	def test_wrongDriverTypeRejected(self):
		with self.assertRaises(ValueError):
			legacy.encodeCommandPayload(legacy.DriverType.SPEECH, RdMessageType.DISPLAY, {"cells": []})
		with self.assertRaises(ValueError):
			legacy.decodeCommandPayload(legacy.DriverType.BRAILLE, SpeechCommand.SPEAK, b"")


class AttributeMessageCodecTests(unittest.TestCase):
	def test_request(self):
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.SPEECH,
			RdMessageType.ATTRIBUTE_REQUEST,
			{"attribute": "language"},
		)
		self.assertEqual(command, legacy.GenericCommand.ATTRIBUTE)
		self.assertEqual(payload, b"`language`")
		self.assertEqual(
			legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
			(RdMessageType.ATTRIBUTE_REQUEST, {"attribute": "language"}),
		)

	def test_value(self):
		command, payload = legacy.encodeCommandPayload(
			legacy.DriverType.SPEECH,
			RdMessageType.ATTRIBUTE_VALUE,
			{"attribute": "language", "value": "nl"},
		)
		self.assertEqual(command, legacy.GenericCommand.ATTRIBUTE)
		self.assertEqual(payload, b"`language`" + _goldenPickle("nl"))
		self.assertEqual(
			legacy.decodeCommandPayload(legacy.DriverType.SPEECH, command, payload),
			(RdMessageType.ATTRIBUTE_VALUE, {"attribute": "language", "value": "nl"}),
		)


class AttributeValueCodecTests(unittest.TestCase):
	def roundTrip(self, attribute: str, value, expectedBytes: bytes):
		encoded = legacy.encodeAttributeValue(attribute, value)
		self.assertEqual(encoded, expectedBytes)
		self.assertEqual(legacy.decodeAttributeValue(attribute, encoded), value)

	def test_versionStrings(self):
		self.roundTrip("nvdaVersion", "2026.1.0", b"2026.1.0")
		self.roundTrip("rdAccessVersion", "1.7.2", b"1.7.2")

	def test_protocolVersion(self):
		self.roundTrip("protocolVersion", 2, b"\x02")

	def test_timeSinceInput(self):
		self.roundTrip("timeSinceInput", 1234, (1234).to_bytes(4, sys.byteorder, signed=False))

	def test_cellCounts(self):
		self.roundTrip("numCells", 40, b"\x28")
		self.roundTrip("numCols", 20, b"\x14")
		self.roundTrip("numRows", 1, b"\x01")

	def test_pickledFallback(self):
		for attribute, value in (
			("language", "nl"),
			("setting_rate", 50),
			("supportedSettings", []),
		):
			with self.subTest(attribute=attribute):
				self.roundTrip(attribute, value, _goldenPickle(value))
