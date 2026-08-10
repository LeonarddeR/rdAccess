# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Tests for the protocol v2 JSON serializer (``lib.protocol.serializer``)."""

from __future__ import annotations

import unittest
from collections import OrderedDict

import inputCore
import speech.commands
from autoSettingsUtils.driverSetting import BooleanDriverSetting, DriverSetting, NumericDriverSetting
from autoSettingsUtils.utils import StringParameterInfo
from lib.protocol.messages import RdMessageType
from lib.protocol.serializer import RdJSONSerializer
from lib.protocol.speech import SpeechAttribute
from logHandler import log
from synthDriverHandler import VoiceInfo


class SerializerTestCase(unittest.TestCase):
	def setUp(self):
		self.serializer = RdJSONSerializer()
		log.records.clear()

	def roundTrip(self, msgType: RdMessageType, **payload) -> dict:
		data = self.serializer.serialize(type=msgType, **payload)
		self.assertTrue(data.endswith(b"\n"))
		self.assertEqual(data[0:1], b"{")
		return self.serializer.deserialize(data)

	def roundTripAttribute(self, attribute: str, value):
		obj = self.roundTrip(RdMessageType.ATTRIBUTE_VALUE, attribute=attribute, value=value)
		self.assertEqual(obj["attribute"], attribute)
		return obj["value"]


class SpeakSequenceTests(SerializerTestCase):
	def test_roundTrip(self):
		sequence = [
			"Hello ",
			speech.commands.IndexCommand(5),
			"world",
			speech.commands.PitchCommand(offset=30),
			speech.commands.EndUtteranceCommand(),
		]
		obj = self.roundTrip(RdMessageType.SPEAK, sequence=sequence)
		# EndUtteranceCommand defines no __eq__, so compare it by type.
		self.assertEqual(obj["sequence"][:-1], sequence[:-1])
		self.assertIs(type(obj["sequence"][-1]), speech.commands.EndUtteranceCommand)

	def test_unknownClassSkipped(self):
		data = b'{"sequence": ["hi", ["NoSuchCommand", {}]], "type": "speak"}\n'
		obj = self.serializer.deserialize(data)
		self.assertEqual(obj["sequence"], ["hi"])
		self.assertTrue(any("NoSuchCommand" in msg for _level, msg in log.records))

	def test_nonSequenceClassSkipped(self):
		"""A class in speech.commands outside SEQUENCE_CLASSES must not be instantiated."""
		data = b'{"sequence": [["NotASpeechCommand", {}]], "type": "speak"}\n'
		obj = self.serializer.deserialize(data)
		self.assertEqual(obj["sequence"], [])


class SupportedSettingsTests(SerializerTestCase):
	def _settings(self) -> list[DriverSetting]:
		return [
			DriverSetting("voice", "&Voice", availableInSettingsRing=True),
			NumericDriverSetting("rate", "&Rate", defaultVal=50),
			BooleanDriverSetting("rateBoost", "Rate boos&t", defaultVal=False),
		]

	def test_roundTrip(self):
		settings = self._settings()
		decoded = self.roundTripAttribute("supportedSettings", settings)
		self.assertEqual(len(decoded), 3)
		for original, new in zip(settings, decoded, strict=True):
			self.assertIs(type(new), type(original))
			expected = {k: v for k, v in original.__dict__.items() if k != "_propertyCache"}
			actual = {k: v for k, v in new.__dict__.items() if k != "_propertyCache"}
			self.assertEqual(actual, expected)

	def test_propertyCacheExcludedAndFresh(self):
		setting = DriverSetting("voice", "&Voice")
		setting._propertyCache[SupportedSettingsTests.test_roundTrip] = "poison"
		(decoded,) = self.roundTripAttribute("supportedSettings", [setting])
		self.assertEqual(len(decoded._propertyCache), 0)

	def test_unknownClassRejected(self):
		data = self.serializer.serialize(
			type=RdMessageType.ATTRIBUTE_VALUE,
			attribute="supportedSettings",
			value=[["Evil", {"id": "x"}]],
		)
		with self.assertRaises(ValueError):
			self.serializer.deserialize(data)


class AvailableValuesTests(SerializerTestCase):
	def test_roundTripPreservesOrderAndTypes(self):
		voices = OrderedDict((
			("zoe", VoiceInfo("zoe", "Zoe", language="en_US")),
			("anna", VoiceInfo("anna", "Anna", language="nl_NL")),
			("plain", StringParameterInfo("plain", "Plain")),
		))
		decoded = self.roundTripAttribute("availableVoices", voices)
		self.assertIsInstance(decoded, OrderedDict)
		self.assertEqual(list(decoded.keys()), list(voices.keys()))
		for key, original in voices.items():
			new = decoded[key]
			self.assertIs(type(new), type(original))
			self.assertEqual(new, original)

	def test_unknownClassRejected(self):
		data = self.serializer.serialize(
			type=RdMessageType.ATTRIBUTE_VALUE,
			attribute="availableVoices",
			value={"x": ["Evil", {"id": "x"}]},
		)
		with self.assertRaises(ValueError):
			self.serializer.deserialize(data)


class SupportedCommandsTests(SerializerTestCase):
	def test_roundTrip(self):
		commands = frozenset((
			speech.commands.IndexCommand,
			speech.commands.PitchCommand,
			speech.commands.BreakCommand,
		))
		decoded = self.roundTripAttribute("supportedCommands", commands)
		self.assertEqual(decoded, commands)

	def test_roundTripMutableSet(self):
		commands = {
			speech.commands.IndexCommand,
			speech.commands.PitchCommand,
			speech.commands.BreakCommand,
		}
		decoded = self.roundTripAttribute("supportedCommands", commands)
		self.assertEqual(decoded, frozenset(commands))

	def test_unknownAndNonCommandNamesDropped(self):
		data = self.serializer.serialize(
			type=RdMessageType.ATTRIBUTE_VALUE,
			attribute="supportedCommands",
			value=["IndexCommand", "NotASpeechCommand", "NoSuchCommand"],
		)
		decoded = self.serializer.deserialize(data)["value"]
		self.assertEqual(decoded, frozenset((speech.commands.IndexCommand,)))


class AvailableLanguagesTests(SerializerTestCase):
	def test_listPassesThroughUntouched(self):
		"""Must not hit _decodeAvailableValues despite naming a language capability."""
		languages = ["en", "nl_NL", None]
		decoded = self.roundTripAttribute(SpeechAttribute.AVAILABLE_LANGUAGES, languages)
		self.assertEqual(decoded, languages)


class GestureMapTests(SerializerTestCase):
	def test_roundTrip(self):
		gestureMap = inputCore.GlobalGestureMap(
			{"globalCommands.GlobalCommands": {"kb:a": "nextHeading", "kb:b": ["one", "two"]}},
		)
		decoded = self.roundTripAttribute("gestureMap", gestureMap)
		self.assertIsInstance(decoded, inputCore.GlobalGestureMap)
		self.assertEqual(decoded.export(), gestureMap.export())

	def test_noneRoundTrip(self):
		self.assertIsNone(self.roundTripAttribute("gestureMap", None))

	def test_wrongClassRejected(self):
		data = self.serializer.serialize(
			type=RdMessageType.ATTRIBUTE_VALUE,
			attribute="gestureMap",
			value=["Evil", {}],
		)
		with self.assertRaises(ValueError):
			self.serializer.deserialize(data)


class ScalarAttributeTests(SerializerTestCase):
	def test_settingValuesPassThrough(self):
		for value in ("espeak", 50, 1.5, True, None):
			with self.subTest(value=value):
				self.assertEqual(self.roundTripAttribute("setting_rate", value), value)

	def test_genericAttributesPassThrough(self):
		self.assertEqual(self.roundTripAttribute("protocolVersion", 2), 2)
		self.assertEqual(self.roundTripAttribute("timeSinceInput", 1234), 1234)
		self.assertEqual(self.roundTripAttribute("language", None), None)


class PlainMessageTests(SerializerTestCase):
	def test_typeIsStringValue(self):
		data = self.serializer.serialize(type=RdMessageType.CANCEL)
		obj = self.serializer.deserialize(data)
		self.assertEqual(obj["type"], "cancel")

	def test_toneAndDisplay(self):
		obj = self.roundTrip(RdMessageType.TONE, hz=440.0, length=100, left=50, right=50)
		self.assertEqual(obj["hz"], 440.0)
		obj = self.roundTrip(RdMessageType.DISPLAY, cells=[0, 1, 255])
		self.assertEqual(obj["cells"], [0, 1, 255])
