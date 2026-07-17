# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for command handler registration and dispatch in RemoteProtocolHandler."""

from __future__ import annotations

import unittest

from lib import protocol
from lib.protocol import legacy
from lib.protocol.messages import RdMessageType

from tests._fakes import FakeHandlerBase, buildMessage

# ATTRIBUTE_SEPARATOR is b"`" (0x60)
_SEP = protocol.ATTRIBUTE_SEPARATOR


def _speakFrame(sequence: list) -> bytes:
	command, payload = legacy.encodeCommandPayload(
		protocol.DriverType.SPEECH,
		RdMessageType.SPEAK,
		{"sequence": sequence},
	)
	return buildMessage(protocol.DriverType.SPEECH, command, payload)


# ---------------------------------------------------------------------------
# Test-local subclasses
# ---------------------------------------------------------------------------


class _SpeakRecorder(FakeHandlerBase):
	"""Records sequences delivered to the SPEAK command handler."""

	def __init__(self):
		super().__init__()
		self.speak_calls: list[list] = []

	@protocol.commandHandler(RdMessageType.SPEAK)
	def _command_speak(self, sequence: list):
		self.speak_calls.append(sequence)


class _MultiCommandRecorder(FakeHandlerBase):
	"""Records dispatches for SPEAK and CANCEL separately."""

	def __init__(self):
		super().__init__()
		self.speak_calls: list[list] = []
		self.cancel_calls: int = 0

	@protocol.commandHandler(RdMessageType.SPEAK)
	def _command_speak(self, sequence: list):
		self.speak_calls.append(sequence)

	@protocol.commandHandler(RdMessageType.CANCEL)
	def _command_cancel(self):
		self.cancel_calls += 1


class _BaseWithCancel(FakeHandlerBase):
	"""Base class that records 'base' when CANCEL is dispatched."""

	def __init__(self):
		super().__init__()
		self.log: list[str] = []

	@protocol.commandHandler(RdMessageType.CANCEL)
	def _command_cancel(self):
		self.log.append("base")


class _SubOverridesCancel(_BaseWithCancel):
	"""Subclass that re-decorates the same method name to record 'sub'."""

	@protocol.commandHandler(RdMessageType.CANCEL)
	def _command_cancel(self):
		self.log.append("sub")


class _Sub2PlainOverride(_BaseWithCancel):
	"""Subclass that shadows _command_cancel with a plain (undecorated) method."""

	def _command_cancel(self):  # plain — not a CommandHandler descriptor
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
		"""_onReceive routes SPEAK to the decorated handler with the decoded sequence."""
		self.handler._onReceive(_speakFrame(["hello"]))
		self.assertEqual(self.handler.speak_calls, [["hello"]])

	def test_speak_handler_called_once_not_multiple_times(self):
		"""Each message produces exactly one handler invocation."""
		self.handler._onReceive(_speakFrame(["world"]))
		self.assertEqual(len(self.handler.speak_calls), 1)


class TestCommandDispatchViaStore(unittest.TestCase):
	"""Direct dispatch through _commandHandlerStore bypasses _onReceive framing."""

	def setUp(self):
		self.handler = _SpeakRecorder()
		self.addCleanup(self.handler.terminate)

	def test_direct_store_call_invokes_handler(self):
		"""Calling the store directly with (messageType, **kwargs) invokes the registered handler."""
		self.handler._commandHandlerStore(RdMessageType.SPEAK, sequence=["x"])
		self.assertEqual(self.handler.speak_calls, [["x"]])


class TestUnknownCommandRaisesNotImplementedError(unittest.TestCase):
	"""Dispatching an unregistered message type raises NotImplementedError from the store."""

	def setUp(self):
		self.handler = _SpeakRecorder()
		self.addCleanup(self.handler.terminate)

	def test_unregistered_command_raises(self):
		"""TONE has no handler in _SpeakRecorder; the store must raise NotImplementedError."""
		with self.assertRaises(NotImplementedError):
			self.handler._commandHandlerStore(RdMessageType.TONE, hz=440.0)


class TestMultipleCommandsRouteCorrectly(unittest.TestCase):
	"""Multiple decorated handlers each receive only their own message type."""

	def setUp(self):
		self.handler = _MultiCommandRecorder()
		self.addCleanup(self.handler.terminate)

	def test_speak_routes_to_speak_handler(self):
		self.handler._commandHandlerStore(RdMessageType.SPEAK, sequence=["speak-payload"])
		self.assertEqual(self.handler.speak_calls, [["speak-payload"]])
		self.assertEqual(self.handler.cancel_calls, 0)

	def test_cancel_routes_to_cancel_handler(self):
		self.handler._commandHandlerStore(RdMessageType.CANCEL)
		self.assertEqual(self.handler.cancel_calls, 1)
		self.assertEqual(self.handler.speak_calls, [])

	def test_both_handlers_independent(self):
		self.handler._commandHandlerStore(RdMessageType.SPEAK, sequence=["s"])
		self.handler._commandHandlerStore(RdMessageType.CANCEL)
		self.assertEqual(self.handler.speak_calls, [["s"]])
		self.assertEqual(self.handler.cancel_calls, 1)


class TestSubclassDecoratorOverride(unittest.TestCase):
	"""A subclass that re-decorates the same method name wins; the base version is replaced."""

	def test_sub_handler_recorded_not_base(self):
		sub = _SubOverridesCancel()
		self.addCleanup(sub.terminate)
		sub._commandHandlerStore(RdMessageType.CANCEL)
		self.assertEqual(sub.log, ["sub"])

	def test_base_handler_still_records_base(self):
		base = _BaseWithCancel()
		self.addCleanup(base.terminate)
		base._commandHandlerStore(RdMessageType.CANCEL)
		self.assertEqual(base.log, ["base"])

	def test_sub_does_not_record_base(self):
		sub = _SubOverridesCancel()
		self.addCleanup(sub.terminate)
		sub._commandHandlerStore(RdMessageType.CANCEL)
		self.assertNotIn("base", sub.log)


class TestPlainOverrideUnregistersCommand(unittest.TestCase):
	"""A plain (undecorated) override of a decorated base method shadows the registration.

	This locks the current semantics: after a plain override the command has no handler.
	"""

	def test_plain_override_causes_not_implemented(self):
		handler = _Sub2PlainOverride()
		self.addCleanup(handler.terminate)
		with self.assertRaises(NotImplementedError):
			handler._commandHandlerStore(RdMessageType.CANCEL)


class TestInstanceIsolation(unittest.TestCase):
	"""Two instances of the same class maintain independent recording state."""

	def setUp(self):
		self.a = _SpeakRecorder()
		self.addCleanup(self.a.terminate)
		self.b = _SpeakRecorder()
		self.addCleanup(self.b.terminate)

	def test_dispatch_to_a_does_not_affect_b(self):
		self.a._commandHandlerStore(RdMessageType.SPEAK, sequence=["for-a"])
		self.assertEqual(self.a.speak_calls, [["for-a"]])
		self.assertEqual(self.b.speak_calls, [])

	def test_dispatch_to_b_does_not_affect_a(self):
		self.b._commandHandlerStore(RdMessageType.SPEAK, sequence=["for-b"])
		self.assertEqual(self.b.speak_calls, [["for-b"]])
		self.assertEqual(self.a.speak_calls, [])


class TestBuiltInAttributeHandler(unittest.TestCase):
	"""ATTRIBUTE frames are normalized into attribute request/value messages.

	When a peer requests NVDA_VERSION (empty rawValue), _handleMessage calls
	_attributeSenderStore which invokes _outgoing_nvdaVersion, which writes the
	version bytes back through FakeIo.  The stubbed versionInfo.version_detailed
	is '2026.1.0-test'.
	"""

	def setUp(self):
		self.handler = FakeHandlerBase()
		self.addCleanup(self.handler.terminate)

	def _make_attribute_request(self, attribute: str) -> bytes:
		"""Build an ATTRIBUTE wire message that requests (empty value) the given attribute name."""
		# payload layout: SEP + attributeName + SEP + rawValue(empty)
		payload = _SEP + attribute.encode("ASCII") + _SEP
		return buildMessage(
			protocol.DriverType.SPEECH,
			protocol.GenericCommand.ATTRIBUTE,
			payload,
		)

	def test_attribute_handler_registered(self):
		"""ATTRIBUTE frames must be dispatchable without NotImplementedError."""
		msg = self._make_attribute_request(protocol.GenericAttribute.NVDA_VERSION)
		# If the handling is missing this raises; we just verify it doesn't.
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
