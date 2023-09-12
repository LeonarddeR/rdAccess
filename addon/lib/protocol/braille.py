# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from enum import Enum, IntEnum
from typing import Optional

import braille
import brailleInput


class BrailleCommand(IntEnum):
    DISPLAY = ord(b"D")
    EXECUTE_GESTURE = ord(b"G")


class BrailleAttribute(bytes, Enum):
    NUM_CELLS = b"numCells"
    GESTURE_MAP = b"gestureMap"
    OBJECT_GESTURE_MAP = b"_gestureMap"


class BrailleInputGesture(
    braille.BrailleDisplayGesture, brailleInput.BrailleInputGesture
):
    def __init__(
        self,
        source: str,
        id: str,
        routingIndex: Optional[int] = None,
        model: Optional[str] = None,
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
