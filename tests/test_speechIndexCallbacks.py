# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Tests for the speech index callback conversion (``lib.protocol.speech``)."""

from __future__ import annotations

import unittest

import speech.commands
from lib.protocol.speech import RemoteIndexCallbackCommand, remapIndexesToCallbacks


class RemapIndexesToCallbacksTests(unittest.TestCase):
	def setUp(self):
		self.reached: list[int] = []

	def _onIndexReached(self, index: int):
		self.reached.append(index)

	def test_indexCommandsReplacedInOrder(self):
		sequence = [
			"Hello ",
			speech.commands.IndexCommand(5),
			"world",
			speech.commands.IndexCommand(7),
		]
		remapped = remapIndexesToCallbacks(sequence, self._onIndexReached)
		self.assertIsInstance(remapped[1], RemoteIndexCallbackCommand)
		self.assertEqual(remapped[1].index, 5)
		self.assertIsInstance(remapped[3], RemoteIndexCallbackCommand)
		self.assertEqual(remapped[3].index, 7)

	def test_nonIndexItemsPassThroughUntouched(self):
		pitch = speech.commands.PitchCommand(offset=30)
		sequence = ["Hello", pitch]
		remapped = remapIndexesToCallbacks(sequence, self._onIndexReached)
		self.assertIs(remapped[0], sequence[0])
		self.assertIs(remapped[1], pitch)

	def test_inputSequenceNotMutated(self):
		index = speech.commands.IndexCommand(5)
		sequence = ["Hello", index]
		remapIndexesToCallbacks(sequence, self._onIndexReached)
		self.assertEqual(len(sequence), 2)
		self.assertIs(sequence[1], index)
		self.assertEqual(index.index, 5)

	def test_doneSpeakingSentinelAppended(self):
		remapped = remapIndexesToCallbacks(["Hello"], self._onIndexReached)
		self.assertEqual(len(remapped), 2)
		sentinel = remapped[-1]
		self.assertIsInstance(sentinel, RemoteIndexCallbackCommand)
		self.assertEqual(sentinel.index, 0)

	def test_runCallsOnIndexReachedWithOriginalIndex(self):
		remapped = remapIndexesToCallbacks([speech.commands.IndexCommand(5)], self._onIndexReached)
		for command in remapped:
			command.run()
		self.assertEqual(self.reached, [5, 0])

	def test_isCallbackCommand(self):
		command = RemoteIndexCallbackCommand(5, self._onIndexReached)
		self.assertIsInstance(command, speech.commands.BaseCallbackCommand)

	def test_reprContainsIndex(self):
		command = RemoteIndexCallbackCommand(5, self._onIndexReached)
		self.assertIn("5", repr(command))
