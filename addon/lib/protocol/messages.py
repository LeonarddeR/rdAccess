# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Message catalog for protocol v2 (JSON Lines).

Message type values marked as mirrored must stay identical to NVDA core's
``_remoteClient.protocol.RemoteMessageType``; conformance tests in
``tests/test_serializerConformance.py`` enforce this.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum

PROTOCOL_VERSION: int = 2

# rd_pipe transport flow control bytes, sent outside any message framing.
MSG_XON = 0x11
MSG_XOFF = 0x13


class DriverType(IntEnum):
	SPEECH = ord(b"S")
	BRAILLE = ord(b"B")


CHANNEL_NAMES: dict[DriverType, str] = {
	DriverType.SPEECH: "NVDA-SPEECH",
	DriverType.BRAILLE: "NVDA-BRAILLE",
}


class GenericAttribute(StrEnum):
	TIME_SINCE_INPUT = "timeSinceInput"
	SUPPORTED_SETTINGS = "supportedSettings"
	NVDA_VERSION = "nvdaVersion"
	RD_ACCESS_VERSION = "rdAccessVersion"
	PROTOCOL_VERSION = "protocolVersion"


class RdMessageType(StrEnum):
	# Mirrored from RemoteMessageType
	PROTOCOL_VERSION = "protocol_version"
	PING = "ping"
	SPEAK = "speak"
	CANCEL = "cancel"
	PAUSE_SPEECH = "pause_speech"
	TONE = "tone"
	WAVE = "wave"
	INDEX = "index"
	DISPLAY = "display"
	BRAILLE_INPUT = "braille_input"

	# RDAccess-specific
	ATTRIBUTE_REQUEST = "attribute_request"
	ATTRIBUTE_VALUE = "attribute_value"
