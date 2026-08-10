# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

from __future__ import annotations

import typing
from enum import IntEnum, StrEnum

from speech.commands import BaseCallbackCommand, IndexCommand

if typing.TYPE_CHECKING:
	from collections.abc import Callable, Iterable, Set as AbstractSet

	from speech.types import SpeechSequence


class SpeechCommand(IntEnum):
	SPEAK = ord(b"S")
	CANCEL = ord(b"C")
	PAUSE = ord(b"P")
	INDEX_REACHED = ord(b"x")
	BEEP = ord(b"B")
	PLAY_WAVE_FILE = ord(b"W")


class SpeechAttribute(StrEnum):
	SUPPORTED_COMMANDS = "supportedCommands"
	LANGUAGE = "language"
	AVAILABLE_LANGUAGES = "_availableLanguages"
	"""Leading underscore keeps the name outside the ``available*s`` setting values namespace."""


def encodeAvailableLanguages(languages: Iterable[str | None]) -> list[str | None]:
	"""Encode an available languages set as a deterministically ordered, JSON-safe list.

	``None`` sorts last.
	"""
	return sorted(languages, key=lambda lang: (lang is None, lang or ""))


def decodeAvailableLanguages(value: object, fallback: AbstractSet[str | None]) -> set[str | None]:
	"""Decode an incoming available languages value to a set.

	Members other than ``str`` and ``None`` are dropped; a malformed or empty value
	decodes to a copy of ``fallback``.
	"""
	if not isinstance(value, (list, tuple, set, frozenset)):
		return set(fallback)
	languages = {lang for lang in value if lang is None or isinstance(lang, str)}
	return languages or set(fallback)


class RemoteIndexCallbackCommand(BaseCallbackCommand):
	"""Calls ``onIndexReached`` with a remote index when speech reaches this command.

	Index 0 doubles as the done speaking sentinel.
	"""

	def __init__(self, index: int, onIndexReached: Callable[[int], None]):
		self.index = index
		self._onIndexReached = onIndexReached

	def run(self):
		self._onIndexReached(self.index)

	def __repr__(self):
		return f"RemoteIndexCallbackCommand({self.index!r})"


def remapIndexesToCallbacks(
	sequence: SpeechSequence,
	onIndexReached: Callable[[int], None],
) -> SpeechSequence:
	"""Return a new sequence with every IndexCommand replaced by a
	:class:`RemoteIndexCallbackCommand` and a done speaking sentinel (index 0) appended.
	"""
	return [
		*(
			RemoteIndexCallbackCommand(item.index, onIndexReached) if isinstance(item, IndexCommand) else item
			for item in sequence
		),
		RemoteIndexCallbackCommand(0, onIndexReached),
	]
