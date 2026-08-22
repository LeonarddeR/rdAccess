# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Unit tests for attribute sender/receiver machinery in lib.protocol."""

from __future__ import annotations

import time
import unittest

from lib import protocol
from lib.protocol import legacy

from tests._fakes import FakeHandlerBase, buildMessage


def _attrRequest(attribute: str) -> bytes:
	"""Raw ATTRIBUTE request message (empty value) as a v1 peer would send it."""
	payload = protocol.ATTRIBUTE_SEPARATOR + attribute.encode("ASCII") + protocol.ATTRIBUTE_SEPARATOR
	return buildMessage(protocol.DriverType.SPEECH, protocol.GenericCommand.ATTRIBUTE, payload)


def _attrPush(attribute: str, value) -> bytes:
	"""Raw ATTRIBUTE value push message as a v1 peer would send it."""
	payload = (
		protocol.ATTRIBUTE_SEPARATOR
		+ attribute.encode("ASCII")
		+ protocol.ATTRIBUTE_SEPARATOR
		+ legacy.encodeAttributeValue(attribute, value)
	)
	return buildMessage(protocol.DriverType.SPEECH, protocol.GenericCommand.ATTRIBUTE, payload)


class LanguageSender(FakeHandlerBase):
	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self) -> str:
		return "nl"


class TestRequestPath(unittest.TestCase):
	"""An incoming attribute request makes the sender store write a reply."""

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


class LanguageReceiver(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue="en")
	def _incoming_language(self, value: str) -> str:
		return value


class TestPushPath(unittest.TestCase):
	"""An incoming attribute push stores the decoded value in the value processor."""

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


_SENTINEL = object()


class LanguageReceiverWithGetter(FakeHandlerBase):
	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE)
	def _incoming_language(self, value: object) -> object:
		return value

	@_incoming_language.defaultValueGetter
	def _default_language(self, _attribute: protocol.AttributeT) -> object:
		return _SENTINEL


class TestDefaultValueGetter(unittest.TestCase):
	"""A defaultValueGetter callable overrides the static defaultValue."""

	def setUp(self):
		self.handler = LanguageReceiverWithGetter()
		self.addCleanup(self.handler.terminate)

	def test_defaultValueGetter_returns_sentinel(self):
		val = self.handler._attributeValueProcessor.getValue(
			protocol.SpeechAttribute.LANGUAGE,
			fallBackToDefault=True,
		)
		self.assertIs(val, _SENTINEL)


class TestFactoryValidation(unittest.TestCase):
	def test_both_defaultValue_and_defaultValueGetter_raises(self):
		with self.assertRaises(ValueError):
			protocol.attributeReceiver("x", defaultValue=1, defaultValueGetter=lambda _s, _a: 2)


class WildcardSettingReceiver(FakeHandlerBase):
	def __init__(self):
		self.wildcard_calls: list[tuple[str, object]] = []
		super().__init__()

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + "*")
	def _incoming_setting(self, attribute: protocol.AttributeT, value: object) -> object:  # type: ignore[override]
		self.wildcard_calls.append((attribute, value))
		return value


class TestWildcardReceiver(unittest.TestCase):
	"""The wildcard catch-all receiver gets the concrete attribute as its first argument."""

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


class WildcardSenderHandler(FakeHandlerBase):
	def __init__(self):
		self.sender_calls: list[str] = []
		super().__init__()

	@protocol.attributeSender("available*s")
	def _outgoing_available(self, attribute: protocol.AttributeT) -> str:
		self.sender_calls.append(attribute)
		return f"data_for_{attribute}"


class TestWildcardSender(unittest.TestCase):
	"""The wildcard sender function receives the concrete attribute it must serve."""

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


class CapsLockToggleReceiver(FakeHandlerBase):
	"""Mirrors the receiver declaration on the client's RemoteHandler."""

	def __init__(self):
		self.callback_calls: list[tuple[protocol.AttributeT, object]] = []
		super().__init__()

	_incoming_capsLockToggle = protocol.AttributeReceiver(
		protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
		defaultValue=None,
	)

	@_incoming_capsLockToggle.updateCallback
	def _cb_capsLockToggle(self, attribute: protocol.AttributeT, value: object) -> None:
		self.callback_calls.append((attribute, value))


def _jsonAttrPush(handler: FakeHandlerBase, attribute: str, value) -> bytes:
	return handler._serializer.serialize(
		type=protocol.RdMessageType.ATTRIBUTE_VALUE,
		attribute=attribute,
		value=value,
	)


class TestCapsLockToggleReceiver(unittest.TestCase):
	"""capsLockToggle is a v2-only attribute; pushes arrive as JSON lines."""

	def setUp(self):
		self.handler = CapsLockToggleReceiver()
		self.addCleanup(self.handler.terminate)

	def test_getValue_fallback_is_none_before_any_push(self):
		"""The None sentinel the client's apply helper tests for."""
		val = self.handler._attributeValueProcessor.getValue(
			protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
			fallBackToDefault=True,
		)
		self.assertIsNone(val)

	def test_json_push_stores_bool_and_fires_callback(self):
		line = _jsonAttrPush(self.handler, protocol.GenericAttribute.CAPS_LOCK_TOGGLE, True)
		self.handler._onReceive(line)
		val = self.handler._attributeValueProcessor.getValue(
			protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
			fallBackToDefault=True,
		)
		self.assertIs(val, True)
		self.assertEqual(
			self.handler.callback_calls,
			[(protocol.GenericAttribute.CAPS_LOCK_TOGGLE, True)],
		)

	def test_json_push_overwrites_previous_value(self):
		self.handler._onReceive(_jsonAttrPush(self.handler, protocol.GenericAttribute.CAPS_LOCK_TOGGLE, True))
		self.handler._onReceive(
			_jsonAttrPush(self.handler, protocol.GenericAttribute.CAPS_LOCK_TOGGLE, False),
		)
		val = self.handler._attributeValueProcessor.getValue(
			protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
			fallBackToDefault=True,
		)
		self.assertIs(val, False)


class CapsLockToggleSender(FakeHandlerBase):
	"""Mirrors the sender declaration on the server's RemoteDriver, minus the OS state read."""

	@protocol.attributeSender(protocol.GenericAttribute.CAPS_LOCK_TOGGLE)
	def _outgoing_capsLockToggle(self) -> bool:
		return True


class TestCapsLockToggleSender(unittest.TestCase):
	def setUp(self):
		self.handler = CapsLockToggleSender()
		self.handler._sendJson = True
		self.addCleanup(self.handler.terminate)

	def test_sender_store_writes_one_json_line(self):
		"""The push path used by the server's _pushCapsLockToggle."""
		self.handler._attributeSenderStore(protocol.GenericAttribute.CAPS_LOCK_TOGGLE)
		self.assertEqual(len(self.handler._dev.writes), 1)
		written = self.handler._dev.writes[0]
		self.assertEqual(written[0:1], b"{")
		obj = self.handler._serializer.deserialize(written)
		self.assertEqual(obj["type"], protocol.RdMessageType.ATTRIBUTE_VALUE.value)
		self.assertEqual(obj["attribute"], protocol.GenericAttribute.CAPS_LOCK_TOGGLE.value)
		self.assertIs(obj["value"], True)


if __name__ == "__main__":
	unittest.main()
