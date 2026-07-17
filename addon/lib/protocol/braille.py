# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from enum import IntEnum, StrEnum

import braille
import brailleInput


class BrailleCommand(IntEnum):
	DISPLAY = ord(b"D")
	EXECUTE_GESTURE = ord(b"G")


class BrailleAttribute(StrEnum):
	NUM_CELLS = "numCells"
	NUM_COLS = "numCols"
	NUM_ROWS = "numRows"
	GESTURE_MAP = "gestureMap"
	OBJECT_GESTURE_MAP = "_gestureMap"


GESTURE_FIELDS = ("source", "id", "routingIndex", "model", "dots", "space")


class BrailleInputGesture(braille.BrailleDisplayGesture, brailleInput.BrailleInputGesture):
	def __init__(
		self,
		source: str,
		id: str,
		routingIndex: int | None = None,
		model: str | None = None,
		dots: int = 0,
		space: bool = False,
		**kwargs,
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
