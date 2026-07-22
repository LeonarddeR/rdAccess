# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit tests for RestrictedUnpickler, the pickle.Unpickler subclass in
addon/lib/protocol/_restrictedUnpickling.py used by lib.protocol.legacy to allowlist
the classes that legitimately cross the RDAccess wire, blocking generic __reduce__-based RCE gadgets.
"""

from __future__ import annotations

import collections
import os
import pickle
import unittest
from typing import Any

from autoSettingsUtils.driverSetting import BooleanDriverSetting, DriverSetting, NumericDriverSetting
from autoSettingsUtils.utils import StringParameterInfo
from inputCore import GlobalGestureMap
from lib.protocol import legacy
from lib.protocol.braille import BrailleInputGesture
from logHandler import log
from speech.commands import IndexCommand, NotASpeechCommand, PitchCommand
from synthDriverHandler import VoiceInfo

# ---------------------------------------------------------------------------
# Helper: mimics a __reduce__-based RCE gadget, the classic pickle attack shape.
# ---------------------------------------------------------------------------


class _ReduceGadget:
	"""Pickles to a call of an arbitrary global with arbitrary args.

	This is the shape a malicious peer would use to smuggle a call to e.g. os.system or
	builtins.eval through pickle.loads; RestrictedUnpickler must refuse to resolve the
	referenced global before the call ever happens.
	"""

	def __init__(self, target: Any, args: tuple = ()):
		self._target = target
		self._args = args

	def __reduce__(self):
		return (self._target, self._args)


# ---------------------------------------------------------------------------
# Rejection cases.
# ---------------------------------------------------------------------------


class TestRestrictedUnpicklingRejections(unittest.TestCase):
	def test_rejects_os_system_reduce_gadget(self):
		"""A payload whose __reduce__ references os.system must not be unpickled."""
		payload = pickle.dumps(_ReduceGadget(os.system, ("echo pwned",)), protocol=4)
		with self.assertRaises(pickle.UnpicklingError):
			legacy.loads(payload)

	def test_rejects_builtins_eval_reduce_gadget(self):
		"""A payload whose __reduce__ references builtins.eval must not be unpickled."""
		payload = pickle.dumps(_ReduceGadget(eval, ("1+1",)), protocol=4)
		with self.assertRaises(pickle.UnpicklingError):
			legacy.loads(payload)

	def test_rejects_non_speechcommand_name_in_speech_commands_module(self):
		"""The dynamic speech.commands rule must refuse names that exist in the module but are not
		SpeechCommand subclasses.
		"""
		payload = pickle.dumps(NotASpeechCommand, protocol=4)
		with self.assertRaises(pickle.UnpicklingError):
			legacy.loads(payload)

	def test_rejects_arbitrary_unknown_class(self):
		"""A class that never crosses the wire legitimately (and isn't in the allowlist) is refused."""
		payload = pickle.dumps(collections.Counter, protocol=4)
		with self.assertRaises(pickle.UnpicklingError):
			legacy.loads(payload)

	def test_rejection_is_logged_as_error(self):
		"""Rejections are logged via log.error, since exceptions raised inside _bgExecutor futures
		are otherwise swallowed silently.
		"""
		log.records.clear()
		payload = pickle.dumps(_ReduceGadget(os.system, ("echo pwned",)), protocol=4)
		with self.assertRaises(pickle.UnpicklingError):
			legacy.loads(payload)
		errorRecords = [msg for level, msg in log.records if level == "error"]
		self.assertTrue(errorRecords, "Expected a log.error call recording the rejected global")
		# os.system's actual module is platform-specific (nt on Windows, posixpath on Unix)
		module_name = os.system.__module__
		self.assertTrue(
			any("system" in msg and module_name in msg for msg in errorRecords),
			"Expected the rejection log to name the offending (module, name)",
		)


# ---------------------------------------------------------------------------
# Acceptance cases: round-trip legacy.dumps -> legacy.loads for everything that legitimately
# crosses the wire (see the audit table in the implementation plan).
# ---------------------------------------------------------------------------


class TestRestrictedUnpicklingAcceptance(unittest.TestCase):
	def _roundtrip(self, obj: Any) -> Any:
		return legacy.loads(legacy.dumps(obj))

	def test_roundtrips_speech_sequence(self):
		original = ["hello", IndexCommand(1), PitchCommand(offset=5)]
		restored = self._roundtrip(original)
		self.assertEqual(restored[0], "hello")
		self.assertIsInstance(restored[1], IndexCommand)
		self.assertEqual(restored[1].index, 1)
		self.assertIsInstance(restored[2], PitchCommand)
		self.assertEqual(restored[2].offset, 5)

	def test_roundtrips_frozenset_of_speech_command_classes(self):
		"""synthDrivers/remote.py._incoming_supportedCommands sends classes, not instances."""
		original = frozenset({IndexCommand, PitchCommand})
		restored = self._roundtrip(original)
		self.assertEqual(restored, original)

	def test_roundtrips_list_of_driver_settings(self):
		original = [
			DriverSetting("id1", "Setting 1"),
			BooleanDriverSetting("id2", "Setting 2", defaultVal=True),
			NumericDriverSetting("id3", "Setting 3", defaultVal=10),
		]
		restored = self._roundtrip(original)
		self.assertEqual(
			[type(o) for o in restored],
			[DriverSetting, BooleanDriverSetting, NumericDriverSetting],
		)
		self.assertEqual(restored[0].id, "id1")
		self.assertEqual(restored[1].defaultVal, True)
		self.assertEqual(restored[2].defaultVal, 10)

	def test_roundtrips_ordered_dict_of_voice_and_string_parameter_info(self):
		original = collections.OrderedDict((
			("voice1", VoiceInfo("voice1", "Voice One", language="en")),
			("param1", StringParameterInfo("param1", "Param One")),
		))
		restored = self._roundtrip(original)
		self.assertIsInstance(restored, collections.OrderedDict)
		self.assertIsInstance(restored["voice1"], VoiceInfo)
		self.assertEqual(restored["voice1"].language, "en")
		self.assertIsInstance(restored["param1"], StringParameterInfo)
		self.assertEqual(restored["param1"].displayName, "Param One")

	def test_roundtrips_global_gesture_map(self):
		original = GlobalGestureMap({"kb:a": "someScript"})
		restored = self._roundtrip(original)
		self.assertIsInstance(restored, GlobalGestureMap)
		self.assertEqual(restored._map, original._map)

	def test_roundtrips_braille_input_gesture(self):
		original = BrailleInputGesture(source="test", id="routing1", routingIndex=3)
		restored = self._roundtrip(original)
		self.assertIsInstance(restored, BrailleInputGesture)
		self.assertEqual(restored.id, "routing1")
		self.assertEqual(restored.routingIndex, 3)

	def test_roundtrips_plain_builtins_dict(self):
		"""Beep/wave-file kwargs are plain builtins; these never touch find_class at all."""
		original = {"frequency": 440, "length": 50, "loop": False, "left": 0.0}
		restored = self._roundtrip(original)
		self.assertEqual(restored, original)


if __name__ == "__main__":
	unittest.main()
