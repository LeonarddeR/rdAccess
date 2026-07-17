# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Conformance tests against NVDA core's Remote Access protocol.

These tests compare RDAccess's protocol v2 with the ``_remoteClient`` modules from the
sibling NVDA source checkout. They fail as soon as the NVDA Remote wire protocol drifts
from what RDAccess mirrors.
"""

from __future__ import annotations

import unittest

from lib.protocol.messages import RdMessageType

from ._nvdaRemote import protocol as nvdaRemoteProtocol


class MessageTypeConformanceTests(unittest.TestCase):
	"""Mirrored message type values must stay identical to RemoteMessageType."""

	MIRRORED_MEMBERS = (
		"PROTOCOL_VERSION",
		"PING",
		"SPEAK",
		"CANCEL",
		"PAUSE_SPEECH",
		"TONE",
		"WAVE",
		"INDEX",
		"DISPLAY",
		"BRAILLE_INPUT",
	)

	def test_mirroredValuesMatchNvdaRemote(self):
		for name in self.MIRRORED_MEMBERS:
			with self.subTest(member=name):
				self.assertEqual(
					RdMessageType[name].value,
					nvdaRemoteProtocol.RemoteMessageType[name].value,
				)

	def test_rdAccessSpecificMembersAbsentFromNvdaRemote(self):
		"""RDAccess-specific types must not collide with names NVDA Remote may assign later
		to different semantics without conformance tests noticing."""
		rdSpecific = set(RdMessageType.__members__) - set(self.MIRRORED_MEMBERS)
		for name in rdSpecific:
			with self.subTest(member=name):
				self.assertNotIn(name, nvdaRemoteProtocol.RemoteMessageType.__members__)
