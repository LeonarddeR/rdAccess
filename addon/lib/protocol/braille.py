# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from enum import Enum, IntEnum
from typing import Any

import brailleInput

from ..nvdaCompat import BrailleDisplayGesture as _BrailleDisplayGesture
from ..nvdaCompat import applyRoutingIndex, getRoutingIndex


class BrailleCommand(IntEnum):
	DISPLAY = ord(b"D")
	EXECUTE_GESTURE = ord(b"G")


class BrailleAttribute(bytes, Enum):
	NUM_CELLS = b"numCells"
	NUM_COLS = b"numCols"
	NUM_ROWS = b"numRows"
	GESTURE_MAP = b"gestureMap"
	OBJECT_GESTURE_MAP = b"_gestureMap"


class BrailleInputGesture(_BrailleDisplayGesture, brailleInput.BrailleInputGesture):
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
		applyRoutingIndex(self, routingIndex)
		self.model = model
		self.dots = dots
		self.space = space
		for attr, val in kwargs.items():
			setattr(self, attr, val)

	def __getstate__(self) -> dict[str, Any]:
		# Carry the routing cell on the wire under a version-neutral key so the receiving NVDA can
		# rebuild whichever of routingIndex/cellIndexes it understands.
		state = self.__dict__.copy()
		for key in ("_propertyCache", "cellIndexes", "routingIndex"):
			state.pop(key, None)
		state["_wireRoutingIndex"] = getRoutingIndex(self)
		return state

	def __setstate__(self, state: dict[str, Any]) -> None:
		routingIndex = state.pop("_wireRoutingIndex", None)
		self.__dict__.update(state)
		applyRoutingIndex(self, routingIndex)
