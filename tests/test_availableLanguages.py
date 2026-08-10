# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for the ``_availableLanguages`` speech attribute helpers in ``lib.protocol.speech``."""

from __future__ import annotations

import unittest

from lib import protocol
from lib.protocol import legacy
from lib.protocol.speech import decodeAvailableLanguages, encodeAvailableLanguages

from tests._fakes import FakeHandlerBase, buildMessage


def _attrPush(attribute: str, value) -> bytes:
	payload = (
		protocol.ATTRIBUTE_SEPARATOR
		+ attribute.encode("ASCII")
		+ protocol.ATTRIBUTE_SEPARATOR
		+ legacy.encodeAttributeValue(attribute, value)
	)
	return buildMessage(protocol.DriverType.SPEECH, protocol.GenericCommand.ATTRIBUTE, payload)


class AttributeNameTests(unittest.TestCase):
	def test_name_outside_settings_namespaces(self):
		"""The wire name must not match the setting_* or available*s wildcard namespaces."""
		from fnmatch import fnmatchcase

		attribute = protocol.SpeechAttribute.AVAILABLE_LANGUAGES
		self.assertEqual(attribute, "_availableLanguages")
		self.assertFalse(fnmatchcase(attribute, "available*s"))
		self.assertFalse(fnmatchcase(attribute, protocol.SETTING_ATTRIBUTE_PREFIX + "*"))


class EncodeTests(unittest.TestCase):
	def test_returns_sorted_list(self):
		self.assertEqual(encodeAvailableLanguages({"nl_NL", "en", "de"}), ["de", "en", "nl_NL"])

	def test_none_sorts_last(self):
		self.assertEqual(encodeAvailableLanguages({None, "nl", "en"}), ["en", "nl", None])


class DecodeTests(unittest.TestCase):
	def test_list_becomes_set(self):
		self.assertEqual(decodeAvailableLanguages(["en", "nl"], {"fr"}), {"en", "nl"})

	def test_set_input_accepted(self):
		"""The legacy pickle path may deliver a set rather than a list."""
		self.assertEqual(decodeAvailableLanguages({"en"}, {"fr"}), {"en"})

	def test_none_member_preserved(self):
		"""A voice without language yields None; a meaningful value, not absence of data."""
		self.assertEqual(decodeAvailableLanguages([None], {"fr"}), {None})

	def test_empty_falls_back(self):
		self.assertEqual(decodeAvailableLanguages([], {"fr"}), {"fr"})

	def test_mapping_falls_back(self):
		"""An old peer's available*s wildcard sender answers with a (possibly empty) dict."""
		self.assertEqual(decodeAvailableLanguages({}, {"fr"}), {"fr"})
		self.assertEqual(decodeAvailableLanguages({"en": "English"}, {"fr"}), {"fr"})

	def test_string_falls_back(self):
		"""A bare string must not be iterated into characters."""
		self.assertEqual(decodeAvailableLanguages("en", {"fr"}), {"fr"})

	def test_non_string_members_dropped(self):
		self.assertEqual(decodeAvailableLanguages(["en", 42], {"fr"}), {"en"})

	def test_only_invalid_members_falls_back(self):
		self.assertEqual(decodeAvailableLanguages([42], {"fr"}), {"fr"})

	def test_fallback_returned_as_copy(self):
		fallback = {"fr"}
		result = decodeAvailableLanguages([], fallback)
		result.add("xx")
		self.assertEqual(fallback, {"fr"})


class AvailableLanguagesReceiver(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.AVAILABLE_LANGUAGES)
	def _incoming_availableLanguages(self, languages) -> set[str | None]:
		return decodeAvailableLanguages(languages, {"en"})

	@_incoming_availableLanguages.defaultValueGetter
	def _default_availableLanguages(self, _attribute: protocol.AttributeT) -> set[str | None]:
		return {"en"}


class ReceiverIntegrationTests(unittest.TestCase):
	def setUp(self):
		self.handler = AvailableLanguagesReceiver()
		self.addCleanup(self.handler.terminate)

	def test_push_stores_normalized_set(self):
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.AVAILABLE_LANGUAGES, ["nl", "de"]))
		value = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.AVAILABLE_LANGUAGES,
			fallBackToDefault=False,
		)
		self.assertEqual(value, {"nl", "de"})

	def test_default_before_first_push(self):
		value = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.AVAILABLE_LANGUAGES,
			fallBackToDefault=True,
		)
		self.assertEqual(value, {"en"})

	def test_pushed_empty_value_stores_fallback(self):
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.AVAILABLE_LANGUAGES, []))
		value = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.AVAILABLE_LANGUAGES,
			fallBackToDefault=False,
		)
		self.assertEqual(value, {"en"})


if __name__ == "__main__":
	unittest.main()
