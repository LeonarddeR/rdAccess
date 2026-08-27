# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Version-gated access to NVDA behavior that differs across the supported NVDA versions.

On NVDA 2026.3 and later the braille symbols live in the ``braille.display``, ``braille.constants`` and
``braille.extensions`` submodules, the former ``brailleInput`` module lives in the ``braille.input``
package, and ``BrailleDisplayGesture`` exposes ``cellIndexes`` (a list) in place of the deprecated
single-valued ``routingIndex``. On 2026.1/2026.2 they are still reached through the ``braille``
facade, the ``brailleInput`` module and ``routingIndex``.

Symbols that do not already name braille are re-exported with a ``braille``/``BRAILLE`` prefix so
they read unambiguously through the ``nvdaCompat`` namespace.
"""

from __future__ import annotations

import buildVersion

_NVDA_2026_3_OR_LATER = (buildVersion.version_year, buildVersion.version_major) >= (2026, 3)
_BRAILLE_IS_PACKAGE = _NVDA_2026_3_OR_LATER
CAPS_LOCK_SYNC_SUPPORTED = _NVDA_2026_3_OR_LATER
"""Whether NVDA passes ``injected`` to ``inputCore.decide_handleRawKey`` handlers, which the
client side of the caps lock synchronization relies on."""

if _BRAILLE_IS_PACKAGE:
	from braille.constants import AUTOMATIC_PORT as BRAILLE_AUTOMATIC_PORT
	from braille.display.driver import BrailleDisplayDriver
	from braille.display.gesture import BrailleDisplayGesture
	from braille.extensions import (
		decide_enabled as braille_decide_enabled,
		displayChanged as braille_displayChanged,
	)
	from braille.input.gesture import BrailleInputGesture
else:
	from braille import (
		AUTOMATIC_PORT as BRAILLE_AUTOMATIC_PORT,
		BrailleDisplayDriver,
		BrailleDisplayGesture,
		decide_enabled as braille_decide_enabled,
		displayChanged as braille_displayChanged,
	)
	from brailleInput import BrailleInputGesture

__all__ = (
	"BRAILLE_AUTOMATIC_PORT",
	"BrailleDisplayDriver",
	"BrailleDisplayGesture",
	"BrailleInputGesture",
	"braille_decide_enabled",
	"braille_displayChanged",
	"getRoutingIndex",
	"applyRoutingIndex",
	"CAPS_LOCK_SYNC_SUPPORTED",
)


def getRoutingIndex(gesture: BrailleDisplayGesture) -> int | None:
	"""Return the routing cell index addressed by ``gesture``, or ``None``.

	On 2026.3+ this reads the highest entry of ``cellIndexes`` (a multi-cell gesture collapses to
	that single index); on older versions it reads ``routingIndex`` directly.
	"""
	if _BRAILLE_IS_PACKAGE:
		cellIndexes = gesture.cellIndexes
		return max(cellIndexes) if cellIndexes else None
	return getattr(gesture, "routingIndex", None)


def applyRoutingIndex(gesture: BrailleDisplayGesture, routingIndex: int | None) -> None:
	"""Store ``routingIndex`` on ``gesture`` using the attribute the running NVDA understands.

	On 2026.3+ this sets ``cellIndexes``; on older versions it sets ``routingIndex``.
	"""
	if _BRAILLE_IS_PACKAGE:
		gesture.cellIndexes = [routingIndex] if routingIndex is not None else None
	else:
		gesture.routingIndex = routingIndex
