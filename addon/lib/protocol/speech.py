import speech
from enum import IntEnum

SPEECH_INDEX_OFFSET = speech.manager.SpeechManager.MAX_INDEX + 1


class SpeechCommand(IntEnum):
	SPEAK = ord(b'S')
	CANCEL = ord(b'C')
	PAUSE = ord(b'P')
	INDEX_REACHED = ord(b'x')


class SpeechAttribute(IntEnum):
	SUPPORTED_COMMANDS = ord(b'C')
	SUPPORTED_SETTINGS = ord(b'S')
	LANGUAGE = ord(b'L')
	AVAILABLE_LANGUAGES = ord(b'l')
	RATE = ord(b'R')
	PITCH = ord(b'P')
	VOLUME = ord(b'o')
	INFLECTION = ord(b'I')
	VOICE = ord(b'V')
	AVAILABLE_VOICES = ord(b'v')
	VARIANT = ord(b'A')
	AVAILABLE_VARIANTS = ord(b'a')
	RATE_BOOST = ord(b'b')
