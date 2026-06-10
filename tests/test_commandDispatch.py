# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for command handler registration and dispatch in RemoteProtocolHandler."""

from __future__ import annotations

import unittest

from lib import protocol

from tests._fakes import FakeHandlerBase, buildMessage

# ATTRIBUTE_SEPARATOR is b"`" (0x60)
_SEP = protocol.ATTRIBUTE_SEPARATOR


# ---------------------------------------------------------------------------
# Test-local subclasses
# ---------------------------------------------------------------------------


class _SpeakRecorder(FakeHandlerBase):
	"""Records payloads delivered to the SPEAK command handler."""

	def __init__(self):
		super().__init__()
		self.speak_calls: list[bytes] = []

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _command_speak(self, payload: bytes):
		self.speak_calls.append(payload)


class _MultiCommandRecorder(FakeHandlerBase):
	"""Records payloads for SPEAK and CANCEL separately."""

	def __init__(self):
		super().__init__()
		self.speak_calls: list[bytes] = []
		self.cancel_calls: list[bytes] = []

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _command_speak(self, payload: bytes):
		self.speak_calls.append(payload)

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _command_cancel(self, payload: bytes):
		self.cancel_calls.append(payload)


class _BaseWithCancel(FakeHandlerBase):
	"""Base class that records 'base' when CANCEL is dispatched."""

	def __init__(self):
		super().__init__()
		self.log: list[str] = []

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _command_cancel(self, _payload: bytes):
		self.log.append("base")


class _SubOverridesCancel(_BaseWithCancel):
	"""Subclass that re-decorates the same method name to record 'sub'."""

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _command_cancel(self, _payload: bytes):
		self.log.append("sub")


class _Sub2PlainOverride(_BaseWithCancel):
	"""Subclass that shadows _command_cancel with a plain (undecorated) method."""

	def _command_cancel(self, _payload: bytes):  # plain — not a CommandHandler descriptor
		self.log.append("plain")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCommandDispatchViaOnReceive(unittest.TestCase):
	"""Dispatch through _onReceive (the normal in-process receive path)."""

	def setUp(self):
		self.handler = _SpeakRecorder()
		self.addCleanup(self.handler.terminate)

	def test_speak_handler_called_once_with_correct_payload(self):
		"""_onReceive routes SPEAK to the decorated handler with the full payload."""
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"hello")
		self.handler._onReceive(msg)
		self.assertEqual(self.handler.speak_calls, [b"hello"])

	def test_speak_handler_called_once_not_multiple_times(self):
		"""Each message produces exactly one handler invocation."""
		msg = buildMessage(protocol.DriverType.SPEECH, protocol.SpeechCommand.SPEAK, b"world")
		self.handler._onReceive(msg)
		self.assertEqual(len(self.handler.speak_calls), 1)


class TestCommandDispatchViaStore(unittest.TestCase):
	"""Direct dispatch through _commandHandlerStore bypasses _onReceive framing."""

	def setUp(self):
		self.handler = _SpeakRecorder()
		self.addCleanup(self.handler.terminate)

	def test_direct_store_call_invokes_handler(self):
		"""Calling the store directly with (command, payload) invokes the registered handler."""
		self.handler._commandHandlerStore(protocol.SpeechCommand.SPEAK, b"x")
		self.assertEqual(self.handler.speak_calls, [b"x"])


class TestUnknownCommandRaisesNotImplementedError(unittest.TestCase):
	"""Dispatching an unregistered command raises NotImplementedError from the store."""

	def setUp(self):
		self.handler = _SpeakRecorder()
		self.addCleanup(self.handler.terminate)

	def test_unregistered_command_raises(self):
		"""BEEP has no handler in _SpeakRecorder; the store must raise NotImplementedError."""
		with self.assertRaises(NotImplementedError):
			self.handler._commandHandlerStore(protocol.SpeechCommand.BEEP, b"")


class TestMultipleCommandsRouteCorrectly(unittest.TestCase):
	"""Multiple decorated handlers each receive only their own command."""

	def setUp(self):
		self.handler = _MultiCommandRecorder()
		self.addCleanup(self.handler.terminate)

	def test_speak_routes_to_speak_handler(self):
		self.handler._commandHandlerStore(protocol.SpeechCommand.SPEAK, b"speak-payload")
		self.assertEqual(self.handler.speak_calls, [b"speak-payload"])
		self.assertEqual(self.handler.cancel_calls, [])

	def test_cancel_routes_to_cancel_handler(self):
		self.handler._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"cancel-payload")
		self.assertEqual(self.handler.cancel_calls, [b"cancel-payload"])
		self.assertEqual(self.handler.speak_calls, [])

	def test_both_handlers_independent(self):
		self.handler._commandHandlerStore(protocol.SpeechCommand.SPEAK, b"s")
		self.handler._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"c")
		self.assertEqual(self.handler.speak_calls, [b"s"])
		self.assertEqual(self.handler.cancel_calls, [b"c"])


class TestSubclassDecoratorOverride(unittest.TestCase):
	"""A subclass that re-decorates the same method name wins; the base version is replaced."""

	def test_sub_handler_recorded_not_base(self):
		sub = _SubOverridesCancel()
		self.addCleanup(sub.terminate)
		sub._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"")
		self.assertEqual(sub.log, ["sub"])

	def test_base_handler_still_records_base(self):
		base = _BaseWithCancel()
		self.addCleanup(base.terminate)
		base._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"")
		self.assertEqual(base.log, ["base"])

	def test_sub_does_not_record_base(self):
		sub = _SubOverridesCancel()
		self.addCleanup(sub.terminate)
		sub._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"")
		self.assertNotIn("base", sub.log)


class TestPlainOverrideUnregistersCommand(unittest.TestCase):
	"""A plain (undecorated) override of a decorated base method shadows the registration.

	This locks the current semantics: after a plain override the command has no handler.
	"""

	def test_plain_override_causes_not_implemented(self):
		handler = _Sub2PlainOverride()
		self.addCleanup(handler.terminate)
		with self.assertRaises(NotImplementedError):
			handler._commandHandlerStore(protocol.SpeechCommand.CANCEL, b"")


class TestInstanceIsolation(unittest.TestCase):
	"""Two instances of the same class maintain independent recording state."""

	def setUp(self):
		self.a = _SpeakRecorder()
		self.addCleanup(self.a.terminate)
		self.b = _SpeakRecorder()
		self.addCleanup(self.b.terminate)

	def test_dispatch_to_a_does_not_affect_b(self):
		self.a._commandHandlerStore(protocol.SpeechCommand.SPEAK, b"for-a")
		self.assertEqual(self.a.speak_calls, [b"for-a"])
		self.assertEqual(self.b.speak_calls, [])

	def test_dispatch_to_b_does_not_affect_a(self):
		self.b._commandHandlerStore(protocol.SpeechCommand.SPEAK, b"for-b")
		self.assertEqual(self.b.speak_calls, [b"for-b"])
		self.assertEqual(self.a.speak_calls, [])


class TestBuiltInAttributeHandler(unittest.TestCase):
	"""GenericCommand.ATTRIBUTE is registered on every subclass.

	When a peer requests NVDA_VERSION (empty rawValue), _command_attribute calls
	_attributeSenderStore which invokes _outgoing_nvdaVersion, which writes the
	version bytes back through FakeIo.  The stubbed versionInfo.version_detailed
	is '2026.1.0-test'.
	"""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def _make_attribute_request(self, attribute: bytes) -> bytes:
		"""Build an ATTRIBUTE wire message that requests (empty value) the given attribute name."""
		# payload layout: SEP + attributeName + SEP + rawValue(empty)
		payload = _SEP + attribute + _SEP
		return buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			payload,
		)

	def test_attribute_handler_registered(self):
		"""ATTRIBUTE command must be dispatchable without NotImplementedError."""
		msg = self._make_attribute_request(protocol.GenericAttribute.NVDA_VERSION)
		# If the handler is missing this raises; we just verify it doesn't.
		self.handler._onReceive(msg)

	def test_nvda_version_request_writes_reply(self):
		"""A NVDA_VERSION attribute request causes a write containing the version string."""
		msg = self._make_attribute_request(protocol.GenericAttribute.NVDA_VERSION)
		self.handler._onReceive(msg)
		self.assertGreater(len(self.handler._dev.writes), 0, "Expected at least one write to FakeIo")
		combined = b"".join(self.handler._dev.writes)
		self.assertIn(b"2026.1.0-test", combined)


if __name__ == "__main__":
	unittest.main()
