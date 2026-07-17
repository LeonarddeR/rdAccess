# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from enum import IntEnum, StrEnum

import speech.manager

SPEECH_INDEX_OFFSET = speech.manager.SpeechManager.MAX_INDEX + 1


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
