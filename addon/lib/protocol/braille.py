import braille
import brailleInput
from enum import IntEnum
from typing import Optional


class BrailleCommand(IntEnum):
	DISPLAY = ord(b'D')
	EXECUTE_GESTURE = ord(b'G')


class BrailleAttribute(IntEnum):
	NUM_CELLS = ord(b'C')
	GESTURE_MAP = ord(b'G')


class BrailleInputGesture(braille.BrailleDisplayGesture, brailleInput.BrailleInputGesture):
	source: str
	model: Optional[str] = None
	id: str
	routingIndex: Optional[int]
