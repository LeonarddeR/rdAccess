# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for attribute sender/receiver machinery in lib.protocol."""

from __future__ import annotations

import time
import unittest

from lib import protocol
from lib.protocol import legacy

from tests._fakes import FakeHandlerBase, buildMessage

# ---------------------------------------------------------------------------
# Helpers: build raw ATTRIBUTE wire messages as a v1 peer would send them.
# ---------------------------------------------------------------------------


def _attrRequest(attribute: str) -> bytes:
	payload = protocol.ATTRIBUTE_SEPARATOR + attribute.encode("ASCII") + protocol.ATTRIBUTE_SEPARATOR
	return buildMessage(protocol.DriverType.SPEECH, protocol.GenericCommand.ATTRIBUTE, payload)


def _attrPush(attribute: str, value) -> bytes:
	payload = (
		protocol.ATTRIBUTE_SEPARATOR
		+ attribute.encode("ASCII")
		+ protocol.ATTRIBUTE_SEPARATOR
		+ legacy.encodeAttributeValue(attribute, value)
	)
	return buildMessage(protocol.DriverType.SPEECH, protocol.GenericCommand.ATTRIBUTE, payload)


# ---------------------------------------------------------------------------
# 1. Request path: sender store produces a reply write.
# ---------------------------------------------------------------------------


class LanguageSender(FakeHandlerBase):
	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self) -> str:
		return "nl"


class TestRequestPath(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageSender()
		self.addCleanup(self.handler.terminate)

	def test_request_triggers_reply_write(self):
		"""Empty-value ATTRIBUTE message causes setRemoteAttribute to be called."""
		self.handler._onReceive(_attrRequest(protocol.SpeechAttribute.LANGUAGE))
		self.assertEqual(len(self.handler._dev.writes), 1)

	def test_reply_payload_contains_attribute_and_value(self):
		"""The written reply embeds ``language`` and the encoded value in its payload."""
		self.handler._onReceive(_attrRequest(protocol.SpeechAttribute.LANGUAGE))
		written = self.handler._dev.writes[0]
		expected_payload = (
			protocol.ATTRIBUTE_SEPARATOR
			+ b"language"
			+ protocol.ATTRIBUTE_SEPARATOR
			+ legacy.encodeAttributeValue(protocol.SpeechAttribute.LANGUAGE, "nl")
		)
		# The written message is a full wire message; the payload starts at byte 4.
		self.assertIn(expected_payload, written)


# ---------------------------------------------------------------------------
# 2. Push path: value processor stores the decoded value.
# ---------------------------------------------------------------------------


class LanguageReceiver(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, value: str) -> str:
		return value


class TestPushPath(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_push_stores_decoded_value(self):
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.LANGUAGE, "nl"))
		value = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=False,
		)
		self.assertEqual(value, "nl")

	def test_push_no_writes(self):
		"""An incoming push must not generate a reply write."""
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.LANGUAGE, "nl"))
		self.assertEqual(self.handler._dev.writes, [])


# ---------------------------------------------------------------------------
# 3. updateCallback fires when a value is pushed.
# ---------------------------------------------------------------------------


class LanguageReceiverWithCallback(FakeHandlerBase):
	def __init__(self):
		self.callback_calls: list[tuple[protocol.AttributeT, object]] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, value: str) -> str:
		return value

	@_incoming_language.updateCallback
	def _cb_language(self, attribute: protocol.AttributeT, value: object) -> None:
		self.callback_calls.append((attribute, value))


class TestUpdateCallback(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiverWithCallback()
		self.addCleanup(self.handler.terminate)

	def test_callback_fires_on_push(self):
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.LANGUAGE, "nl"))
		self.assertEqual(len(self.handler.callback_calls), 1)
		attr, val = self.handler.callback_calls[0]
		self.assertEqual(attr, protocol.SpeechAttribute.LANGUAGE)
		self.assertEqual(val, "nl")

	def test_callback_fires_on_setValue(self):
		self.handler._attributeValueProcessor.setValue(protocol.SpeechAttribute.LANGUAGE, "de")
		self.assertEqual(len(self.handler.callback_calls), 1)
		attr, val = self.handler.callback_calls[0]
		self.assertEqual(attr, protocol.SpeechAttribute.LANGUAGE)
		self.assertEqual(val, "de")

	def test_callback_records_correct_value_inside_body(self):
		"""Callback body sees exactly the value that was pushed, not stale state."""
		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.LANGUAGE, "fr"))
		self.assertEqual(self.handler.callback_calls[-1], (protocol.SpeechAttribute.LANGUAGE, "fr"))


# ---------------------------------------------------------------------------
# 4. defaultValue: _getDefaultAttributeValue and getValue fallback.
# ---------------------------------------------------------------------------


class TestDefaultValue(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_getDefaultAttributeValue_returns_declared_default(self):
		val = self.handler._attributeValueProcessor._getDefaultAttributeValue(
			protocol.SpeechAttribute.LANGUAGE,
		)
		self.assertEqual(val, "en")

	def test_getValue_fallback_returns_default(self):
		val = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=True,
		)
		self.assertEqual(val, "en")

	def test_getValue_fallback_caches_default(self):
		"""After a fallback getValue, a non-fallback getValue must succeed."""
		self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=True,
		)
		val = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=False,
		)
		self.assertEqual(val, "en")

	def test_getValue_no_fallback_raises_before_any_push(self):
		with self.assertRaises(KeyError):
			self.handler._attributeValueProcessor.getValue(
				protocol.SpeechAttribute.LANGUAGE,
				fallBackToDefault=False,
			)


# ---------------------------------------------------------------------------
# 5. defaultValueGetter: custom callable overrides the static defaultValue.
# ---------------------------------------------------------------------------

_SENTINEL = object()


class LanguageReceiverWithGetter(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE)
	def _incoming_language(self, value: object) -> object:
		return value

	@_incoming_language.defaultValueGetter
	def _default_language(self, _attribute: protocol.AttributeT) -> object:
		return _SENTINEL


class TestDefaultValueGetter(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiverWithGetter()
		self.addCleanup(self.handler.terminate)

	def test_defaultValueGetter_returns_sentinel(self):
		val = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=True,
		)
		self.assertIs(val, _SENTINEL)


# ---------------------------------------------------------------------------
# 6. Factory validation: both defaultValue and defaultValueGetter → ValueError.
# ---------------------------------------------------------------------------


class TestFactoryValidation(unittest.TestCase):
	def test_both_defaultValue_and_defaultValueGetter_raises(self):
		with self.assertRaises(ValueError):
			protocol.attributeReceiver("x", defaultValue=1, defaultValueGetter=lambda _s, _a: 2)


# ---------------------------------------------------------------------------
# 7. Wildcard receiver: catch-all receives concrete attribute as first arg.
# ---------------------------------------------------------------------------


class WildcardSettingReceiver(FakeHandlerBase):
	def __init__(self):
		self.wildcard_calls: list[tuple[str, object]] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + "*")
	def _incoming_setting(self, attribute: protocol.AttributeT, value: object) -> object:  # type: ignore[override]
		self.wildcard_calls.append((attribute, value))
		return value


class TestWildcardReceiver(unittest.TestCase):
	def setUp(self):
		self.handler = WildcardSettingReceiver()
		self.addCleanup(self.handler.terminate)

	def test_wildcard_invoked_with_concrete_attribute(self):
		self.handler._onReceive(_attrPush("setting_rate", 50))
		self.assertEqual(len(self.handler.wildcard_calls), 1)
		attr, value = self.handler.wildcard_calls[0]
		self.assertEqual(attr, "setting_rate")
		self.assertEqual(value, 50)

	def test_value_stored_under_concrete_attribute(self):
		self.handler._onReceive(_attrPush("setting_rate", 50))
		val = self.handler._attributeValueProcessor.getValue("setting_rate", fallBackToDefault=False)
		self.assertEqual(val, 50)


# ---------------------------------------------------------------------------
# 8. Exact beats wildcard for setting_voice.
# ---------------------------------------------------------------------------


class ExactBeatWildcardReceiver(FakeHandlerBase):
	def __init__(self):
		self.wildcard_calls: list[tuple[str, object]] = []
		self.exact_calls: list[object] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + "*")
	def _incoming_setting(self, attribute: protocol.AttributeT, value: object) -> object:  # type: ignore[override]
		self.wildcard_calls.append((attribute, value))
		return value

	@protocol.attributeReceiver("setting_voice", defaultValue=None)
	def _incoming_setting_voice(self, value: object) -> object:
		self.exact_calls.append(value)
		return value


class TestExactBeatsWildcard(unittest.TestCase):
	def setUp(self):
		self.handler = ExactBeatWildcardReceiver()
		self.addCleanup(self.handler.terminate)

	def test_exact_handler_invoked_for_setting_voice(self):
		self.handler._onReceive(_attrPush("setting_voice", "David"))
		self.assertEqual(self.handler.exact_calls, ["David"])

	def test_wildcard_not_invoked_for_setting_voice(self):
		self.handler._onReceive(_attrPush("setting_voice", "David"))
		self.assertEqual(self.handler.wildcard_calls, [])

	def test_wildcard_still_handles_other_settings(self):
		self.handler._onReceive(_attrPush("setting_rate", 75))
		self.assertEqual(len(self.handler.wildcard_calls), 1)
		self.assertEqual(self.handler.exact_calls, [])


# ---------------------------------------------------------------------------
# 9. Wildcard sender: function receives concrete attribute.
# ---------------------------------------------------------------------------


class WildcardSenderHandler(FakeHandlerBase):
	def __init__(self):
		self.sender_calls: list[str] = []
		super().__init__()

	@protocol.attributeSender("available*s")
	def _outgoing_available(self, attribute: protocol.AttributeT) -> str:
		self.sender_calls.append(attribute)
		return f"data_for_{attribute}"


class TestWildcardSender(unittest.TestCase):
	def setUp(self):
		self.handler = WildcardSenderHandler()
		self.addCleanup(self.handler.terminate)

	def test_wildcard_sender_writes_reply(self):
		self.handler._attributeSenderStore("availableVoices")
		self.assertEqual(len(self.handler._dev.writes), 1)

	def test_wildcard_sender_receives_concrete_attribute(self):
		self.handler._attributeSenderStore("availableVoices")
		self.assertEqual(self.handler.sender_calls, ["availableVoices"])

	def test_wildcard_sender_reply_contains_concrete_attribute(self):
		self.handler._attributeSenderStore("availableVoices")
		written = self.handler._dev.writes[0]
		self.assertIn(b"availableVoices", written)

	def test_wildcard_sender_reply_contains_value(self):
		self.handler._attributeSenderStore("availableVoices")
		written = self.handler._dev.writes[0]
		# The value is pickled; the string's UTF-8 bytes appear inside the pickle.
		self.assertIn(b"data_for_availableVoices", written)


# ---------------------------------------------------------------------------
# 10. isAttributeSupported.
# ---------------------------------------------------------------------------


class TestIsAttributeSupported(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageSender()
		self.addCleanup(self.handler.terminate)
		self.receiver_handler = LanguageReceiver()
		self.addCleanup(self.receiver_handler.terminate)

	def test_exact_sender_supported(self):
		self.assertTrue(
			self.handler._attributeSenderStore.isAttributeSupported(protocol.SpeechAttribute.LANGUAGE),
		)

	def test_unknown_sender_not_supported(self):
		self.assertFalse(
			self.handler._attributeSenderStore.isAttributeSupported("unknownAttribute"),
		)

	def test_exact_receiver_supported(self):
		self.assertTrue(
			self.receiver_handler._attributeValueProcessor.isAttributeSupported(
				protocol.SpeechAttribute.LANGUAGE,
			),
		)

	def test_unknown_receiver_not_supported(self):
		self.assertFalse(
			self.receiver_handler._attributeValueProcessor.isAttributeSupported("unknownAttribute"),
		)

	def test_wildcard_receiver_matched_supported(self):
		handler = WildcardSettingReceiver()
		self.addCleanup(handler.terminate)
		self.assertTrue(
			handler._attributeValueProcessor.isAttributeSupported("setting_pitch"),
		)


# ---------------------------------------------------------------------------
# 11. Unknown attribute dispatch raises NotImplementedError.
# ---------------------------------------------------------------------------


class TestUnknownAttributeDispatch(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_unknown_receiver_raises(self):
		with self.assertRaises(NotImplementedError):
			self.handler._attributeValueProcessor("nope", "v")

	def test_unknown_sender_raises(self):
		with self.assertRaises(NotImplementedError):
			self.handler._attributeSenderStore("nope")


# ---------------------------------------------------------------------------
# 12. hasNewValueSince.
# ---------------------------------------------------------------------------


class TestHasNewValueSince(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_has_new_value_after_setValue(self):
		t = time.perf_counter()
		self.handler._attributeValueProcessor.setValue(protocol.SpeechAttribute.LANGUAGE, "nl")
		self.assertTrue(
			self.handler._attributeValueProcessor.hasNewValueSince(
				protocol.SpeechAttribute.LANGUAGE,
				t,
			),
		)

	def test_no_new_value_for_never_set_attribute(self):
		t = time.perf_counter()
		self.assertFalse(
			self.handler._attributeValueProcessor.hasNewValueSince(
				protocol.SpeechAttribute.LANGUAGE,
				t,
			),
		)


# ---------------------------------------------------------------------------
# 13. clearValue and clearCache.
# ---------------------------------------------------------------------------


class TestClearValueAndCache(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_clearValue_then_getValue_raises_KeyError(self):
		self.handler._attributeValueProcessor.setValue(protocol.SpeechAttribute.LANGUAGE, "nl")
		self.handler._attributeValueProcessor.clearValue(protocol.SpeechAttribute.LANGUAGE)
		with self.assertRaises(KeyError):
			self.handler._attributeValueProcessor.getValue(
				protocol.SpeechAttribute.LANGUAGE,
				fallBackToDefault=False,
			)

	def test_clearCache_clears_values(self):
		self.handler._attributeValueProcessor.setValue(protocol.SpeechAttribute.LANGUAGE, "nl")
		self.handler._attributeValueProcessor.clearCache()
		with self.assertRaises(KeyError):
			self.handler._attributeValueProcessor.getValue(
				protocol.SpeechAttribute.LANGUAGE,
				fallBackToDefault=False,
			)

	def test_clearCache_clears_pending_flag(self):
		self.handler._attributeValueProcessor.setAttributeRequestPending(
			protocol.SpeechAttribute.LANGUAGE,
		)
		self.assertTrue(
			self.handler._attributeValueProcessor.isAttributeRequestPending(
				protocol.SpeechAttribute.LANGUAGE,
			),
		)
		self.handler._attributeValueProcessor.clearCache()
		self.assertFalse(
			self.handler._attributeValueProcessor.isAttributeRequestPending(
				protocol.SpeechAttribute.LANGUAGE,
			),
		)


# ---------------------------------------------------------------------------
# 14. setAttributeRequestPending cleared by an incoming push.
# ---------------------------------------------------------------------------


class TestPendingCleared(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_pending_set_then_push_clears_it(self):
		avp = self.handler._attributeValueProcessor
		avp.setAttributeRequestPending(protocol.SpeechAttribute.LANGUAGE)
		self.assertTrue(avp.isAttributeRequestPending(protocol.SpeechAttribute.LANGUAGE))

		self.handler._onReceive(_attrPush(protocol.SpeechAttribute.LANGUAGE, "nl"))
		self.assertFalse(avp.isAttributeRequestPending(protocol.SpeechAttribute.LANGUAGE))


if __name__ == "__main__":
	unittest.main()
