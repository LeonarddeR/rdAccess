# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for attribute sender/receiver machinery in lib.protocol."""

from __future__ import annotations

import time
import unittest

from lib import protocol

from tests._fakes import FakeHandlerBase, buildMessage

# ---------------------------------------------------------------------------
# Helper: build a raw ATTRIBUTE payload as the wire expects it.
# ---------------------------------------------------------------------------


def _attrPayload(attribute: bytes, value: bytes = b"") -> bytes:
	"""Return the payload bytes that _command_attribute parses."""
	return protocol.ATTRIBUTE_SEPARATOR + attribute + protocol.ATTRIBUTE_SEPARATOR + value


# ---------------------------------------------------------------------------
# 1. Request path: sender store produces a reply write.
# ---------------------------------------------------------------------------


class LanguageSender(FakeHandlerBase):
	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self) -> bytes:
		return b"nl"


class TestRequestPath(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageSender()
		self.addCleanup(self.handler.terminate)

	def test_request_triggers_reply_write(self):
		"""Empty-value ATTRIBUTE message causes setRemoteAttribute to be called."""
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE),
		)
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler._dev.writes), 1)

	def test_reply_payload_contains_attribute_and_value(self):
		"""The written reply embeds ``language`` and ``nl`` in its payload."""
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE),
		)
		self.handler._onReceive(msg)
		written = self.handler._dev.writes[0]
		expected_payload = _attrPayload(protocol.SpeechAttribute.LANGUAGE, b"nl")
		# The written message is a full wire message; the payload starts at byte 4.
		self.assertIn(expected_payload, written)


# ---------------------------------------------------------------------------
# 2. Push path: value processor stores the decoded value.
# ---------------------------------------------------------------------------


class LanguageReceiver(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, payload: bytes) -> str:
		return payload.decode()


class TestPushPath(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiver()
		self.addCleanup(self.handler.terminate)

	def test_push_stores_decoded_value(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE, b"nl"),
		)
		self.handler._onReceive(msg)
		value = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=False,
		)
		self.assertEqual(value, "nl")

	def test_push_no_writes(self):
		"""An incoming push must not generate a reply write."""
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE, b"nl"),
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler._dev.writes, [])


# ---------------------------------------------------------------------------
# 3. updateCallback fires when a value is pushed.
# ---------------------------------------------------------------------------


class LanguageReceiverWithCallback(FakeHandlerBase):
	def __init__(self):
		self.callback_calls: list[tuple[protocol.AttributeT, object]] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, payload: bytes) -> str:
		return payload.decode()

	@_incoming_language.updateCallback
	def _cb_language(self, attribute: protocol.AttributeT, value: object) -> None:
		self.callback_calls.append((attribute, value))


class TestUpdateCallback(unittest.TestCase):
	def setUp(self):
		self.handler = LanguageReceiverWithCallback()
		self.addCleanup(self.handler.terminate)

	def test_callback_fires_on_push(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE, b"nl"),
		)
		self.handler._onReceive(msg)
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
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE, b"fr"),
		)
		self.handler._onReceive(msg)
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
	def _incoming_language(self, payload: bytes) -> object:
		return payload.decode()

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
			protocol.attributeReceiver(b"x", defaultValue=1, defaultValueGetter=lambda _s, _a: 2)


# ---------------------------------------------------------------------------
# 7. Wildcard receiver: catch-all receives concrete attribute as first arg.
# ---------------------------------------------------------------------------


class WildcardSettingReceiver(FakeHandlerBase):
	def __init__(self):
		self.wildcard_calls: list[tuple[bytes, bytes]] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, attribute: protocol.AttributeT, payload: bytes) -> bytes:  # type: ignore[override]
		self.wildcard_calls.append((bytes(attribute), payload))
		return payload


class TestWildcardReceiver(unittest.TestCase):
	def setUp(self):
		self.handler = WildcardSettingReceiver()
		self.addCleanup(self.handler.terminate)

	def test_wildcard_invoked_with_concrete_attribute(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(b"setting_rate", b"50"),
		)
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler.wildcard_calls), 1)
		attr, payload = self.handler.wildcard_calls[0]
		self.assertEqual(attr, b"setting_rate")
		self.assertEqual(payload, b"50")

	def test_value_stored_under_concrete_attribute(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(b"setting_rate", b"50"),
		)
		self.handler._onReceive(msg)
		val = self.handler._attributeValueProcessor.getValue(b"setting_rate", fallBackToDefault=False)
		self.assertEqual(val, b"50")


# ---------------------------------------------------------------------------
# 8. Exact beats wildcard for setting_voice.
# ---------------------------------------------------------------------------


class ExactBeatWildcardReceiver(FakeHandlerBase):
	def __init__(self):
		self.wildcard_calls: list[tuple[bytes, bytes]] = []
		self.exact_calls: list[bytes] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, attribute: protocol.AttributeT, payload: bytes) -> bytes:  # type: ignore[override]
		self.wildcard_calls.append((bytes(attribute), payload))
		return payload

	@protocol.attributeReceiver(b"setting_voice", defaultValue=None)
	def _incoming_setting_voice(self, payload: bytes) -> bytes:
		self.exact_calls.append(payload)
		return payload


class TestExactBeatsWildcard(unittest.TestCase):
	def setUp(self):
		self.handler = ExactBeatWildcardReceiver()
		self.addCleanup(self.handler.terminate)

	def test_exact_handler_invoked_for_setting_voice(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(b"setting_voice", b"David"),
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.exact_calls, [b"David"])

	def test_wildcard_not_invoked_for_setting_voice(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(b"setting_voice", b"David"),
		)
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.wildcard_calls, [])

	def test_wildcard_still_handles_other_settings(self):
		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(b"setting_rate", b"75"),
		)
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler.wildcard_calls), 1)
		self.assertEqual(self.handler.exact_calls, [])


# ---------------------------------------------------------------------------
# 9. Wildcard sender: function receives concrete attribute.
# ---------------------------------------------------------------------------


class WildcardSenderHandler(FakeHandlerBase):
	def __init__(self):
		self.sender_calls: list[bytes] = []
		super().__init__()

	@protocol.attributeSender(b"available*s")
	def _outgoing_available(self, attribute: protocol.AttributeT) -> bytes:
		self.sender_calls.append(bytes(attribute))
		return b"data_for_" + bytes(attribute)


class TestWildcardSender(unittest.TestCase):
	def setUp(self):
		self.handler = WildcardSenderHandler()
		self.addCleanup(self.handler.terminate)

	def test_wildcard_sender_writes_reply(self):
		self.handler._attributeSenderStore(b"availableVoices")
		self.assertEqual(len(self.handler._dev.writes), 1)

	def test_wildcard_sender_receives_concrete_attribute(self):
		self.handler._attributeSenderStore(b"availableVoices")
		self.assertEqual(self.handler.sender_calls, [b"availableVoices"])

	def test_wildcard_sender_reply_contains_concrete_attribute(self):
		self.handler._attributeSenderStore(b"availableVoices")
		written = self.handler._dev.writes[0]
		self.assertIn(b"availableVoices", written)

	def test_wildcard_sender_reply_contains_value(self):
		self.handler._attributeSenderStore(b"availableVoices")
		written = self.handler._dev.writes[0]
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
			self.handler._attributeSenderStore.isAttributeSupported(b"unknownAttribute"),
		)

	def test_exact_receiver_supported(self):
		self.assertTrue(
			self.receiver_handler._attributeValueProcessor.isAttributeSupported(
				protocol.SpeechAttribute.LANGUAGE,
			),
		)

	def test_unknown_receiver_not_supported(self):
		self.assertFalse(
			self.receiver_handler._attributeValueProcessor.isAttributeSupported(b"unknownAttribute"),
		)

	def test_wildcard_receiver_matched_supported(self):
		handler = WildcardSettingReceiver()
		self.addCleanup(handler.terminate)
		self.assertTrue(
			handler._attributeValueProcessor.isAttributeSupported(b"setting_pitch"),
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
			self.handler._attributeValueProcessor(b"nope", b"v")

	def test_unknown_sender_raises(self):
		with self.assertRaises(NotImplementedError):
			self.handler._attributeSenderStore(b"nope")


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

		msg = buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			_attrPayload(protocol.SpeechAttribute.LANGUAGE, b"nl"),
		)
		self.handler._onReceive(msg)
		self.assertFalse(avp.isAttributeRequestPending(protocol.SpeechAttribute.LANGUAGE))


if __name__ == "__main__":
	unittest.main()
