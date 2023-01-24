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

	def __init__(
			self,
			source: str,
			id: str,
			routingIndex: Optional[int] = None,
			model: Optional[str] = None,
			dots: int = 0,
			space: bool = False,
			**kwargs
	):
		super().__init__()
		self.source = source
		self.id = id
		self.routingIndex = routingIndex
		self.model = model
		self.dots = dots
		self.space = space
		for attr, val in kwargs.items():
			setattr(self, attr, val)
