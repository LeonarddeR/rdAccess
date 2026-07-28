# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Integration tests feeding converted remote sequences through the real NVDA SpeechManager.

``speech.manager`` is imported for real from the sibling NVDA source checkout (see
:mod:`tests._stubs`), so these tests exercise the actual callback-to-index conversion,
index dispatch and cancel behavior the client relies on.
"""

from __future__ import annotations

import importlib
import unittest

import queueHandler
import speech.commands
import synthDriverHandler
from lib.protocol.speech import remapIndexesToCallbacks

speechManager = importlib.import_module("speech.manager")

from speech.priorities import Spri  # noqa: E402


class FakeSynth:
	def __init__(self):
		self.spoken: list[list] = []
		self.cancelCount = 0

	def speak(self, sequence: list):
		self.spoken.append(sequence)

	def cancel(self):
		self.cancelCount += 1


class SpeechManagerIntegrationTests(unittest.TestCase):
	def setUp(self):
		self.reached: list[int] = []
		self.synth = FakeSynth()
		synthDriverHandler._currentSynth = self.synth
		self.manager = speechManager.SpeechManager()

	def tearDown(self):
		synthDriverHandler._currentSynth = None

	def _speakRemapped(self, sequence: list) -> list:
		"""Speak a converted remote sequence and return the utterance pushed to the synth."""
		self.manager.speak(remapIndexesToCallbacks(sequence, self.reached.append), priority=Spri.NORMAL)
		return self.synth.spoken[-1]

	def _synthIndexes(self, utterance: list) -> list[int]:
		return [item.index for item in utterance if isinstance(item, speech.commands.IndexCommand)]

	def _reachIndex(self, index: int):
		synthDriverHandler.synthIndexReached.notify(synth=self.synth, index=index)
		queueHandler.pumpAll()

	def test_remoteIndexesReportedInOrderWithDoneSpeakingSentinel(self):
		utterance = self._speakRemapped(
			["Hello", speech.commands.IndexCommand(5), "world", speech.commands.IndexCommand(7)],
		)
		for index in self._synthIndexes(utterance):
			self._reachIndex(index)
		self.assertEqual(self.reached, [5, 7, 0])

	def test_synthOnlyReceivesManagerAllocatedIndexes(self):
		utterance = self._speakRemapped(["Hello", speech.commands.IndexCommand(5000)])
		indexes = self._synthIndexes(utterance)
		self.assertNotIn(5000, indexes)
		self.assertTrue(all(0 < index <= speechManager.SpeechManager.MAX_INDEX for index in indexes))

	def test_cancelDropsPendingCallbacks(self):
		utterance = self._speakRemapped(
			["Hello", speech.commands.IndexCommand(5), "world", speech.commands.IndexCommand(7)],
		)
		indexes = self._synthIndexes(utterance)
		self._reachIndex(indexes[0])
		self.manager.cancel()
		for index in indexes[1:]:
			self._reachIndex(index)
		self.assertEqual(self.reached, [5])
		self.assertEqual(self.synth.cancelCount, 1)

	def test_speaksNormallyAfterCancel(self):
		self._speakRemapped(["Hello", speech.commands.IndexCommand(5)])
		self.manager.cancel()
		utterance = self._speakRemapped(["again", speech.commands.IndexCommand(6)])
		for index in self._synthIndexes(utterance):
			self._reachIndex(index)
		self.assertEqual(self.reached, [6, 0])
