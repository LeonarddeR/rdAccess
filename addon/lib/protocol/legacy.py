# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Legacy (protocol v1) wire format codecs.

Protocol v1 frames messages as ``[driverType:1][command:1][payloadLen:2 LE][payload]``
with pickled payloads for non-trivial values. This module translates between those
byte formats and the value-based messages (:class:`RdMessageType` plus kwargs) used
by the rest of the protocol package, so a single dispatch path serves both the legacy
and the JSON Lines stack. Payloads are unpickled through the allowlist-restricted
unpickler only.
"""

from __future__ import annotations

import pickle
import sys
from collections.abc import Callable
from enum import IntEnum
from typing import Any

from ._restrictedUnpickling import restrictedLoads
from .braille import GESTURE_FIELDS, BrailleCommand, BrailleInputGesture
from .messages import DriverType, RdMessageType
from .speech import SpeechCommand

__all__ = [
	"ATTRIBUTE_SEPARATOR",
	"MSG_XOFF",
	"MSG_XON",
	"DriverType",
	"GenericCommand",
	"decodeAttributeValue",
	"decodeCommandPayload",
	"encodeAttributeValue",
	"encodeCommandPayload",
	"packFrame",
	"restrictedLoads",
]

ATTRIBUTE_SEPARATOR = b"`"
MSG_XON = 0x11
MSG_XOFF = 0x13


class GenericCommand(IntEnum):
	ATTRIBUTE = ord(b"@")


def dumps(obj: Any) -> bytes:
	return pickle.dumps(obj, protocol=4)


def packFrame(driverType: int, command: int, payload: bytes = b"") -> bytes:
	return bytes((
		driverType,
		command,
		*len(payload).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
		*payload,
	))


def _decodeKwargs(payload: bytes) -> dict[str, Any]:
	kwargs = restrictedLoads(payload)
	if not isinstance(kwargs, dict):
		raise ValueError(f"Expected pickled kwargs, got {kwargs!r}")
	return kwargs


def _encodeBrailleInput(payload: dict[str, Any]) -> bytes:
	return dumps(BrailleInputGesture(**payload))


def _decodeBrailleInput(payload: bytes) -> dict[str, Any]:
	gesture = restrictedLoads(payload)
	if not isinstance(gesture, BrailleInputGesture):
		raise ValueError(f"Expected a pickled BrailleInputGesture, got {gesture!r}")
	return {field: getattr(gesture, field, None) for field in GESTURE_FIELDS}


_PAYLOAD_CODECS: dict[
	RdMessageType,
	tuple[Callable[[dict[str, Any]], bytes], Callable[[bytes], dict[str, Any]]],
] = {
	RdMessageType.SPEAK: (
		lambda p: dumps(p["sequence"]),
		lambda b: {"sequence": restrictedLoads(b)},
	),
	RdMessageType.CANCEL: (lambda _p: b"", lambda _b: {}),
	RdMessageType.PAUSE_SPEECH: (
		lambda p: bool(p["switch"]).to_bytes(length=1, byteorder=sys.byteorder),
		lambda b: {"switch": bool(b[0])},
	),
	RdMessageType.INDEX: (
		lambda p: int(p["index"]).to_bytes(length=2, byteorder=sys.byteorder, signed=False),
		lambda b: {"index": int.from_bytes(b, byteorder=sys.byteorder, signed=False)},
	),
	RdMessageType.TONE: (dumps, _decodeKwargs),
	RdMessageType.WAVE: (dumps, _decodeKwargs),
	RdMessageType.DISPLAY: (
		lambda p: bytes(p["cells"]),
		lambda b: {"cells": list(b)},
	),
	RdMessageType.BRAILLE_INPUT: (_encodeBrailleInput, _decodeBrailleInput),
}

_COMMAND_TO_MESSAGE: dict[DriverType, dict[int, RdMessageType]] = {
	DriverType.SPEECH: {
		SpeechCommand.SPEAK: RdMessageType.SPEAK,
		SpeechCommand.CANCEL: RdMessageType.CANCEL,
		SpeechCommand.PAUSE: RdMessageType.PAUSE_SPEECH,
		SpeechCommand.INDEX_REACHED: RdMessageType.INDEX,
		SpeechCommand.BEEP: RdMessageType.TONE,
		SpeechCommand.PLAY_WAVE_FILE: RdMessageType.WAVE,
	},
	DriverType.BRAILLE: {
		BrailleCommand.DISPLAY: RdMessageType.DISPLAY,
		BrailleCommand.EXECUTE_GESTURE: RdMessageType.BRAILLE_INPUT,
	},
}
_MESSAGE_TO_COMMAND: dict[DriverType, dict[RdMessageType, int]] = {
	driverType: {msgType: command for command, msgType in mapping.items()}
	for driverType, mapping in _COMMAND_TO_MESSAGE.items()
}


def _intCodec(length: int) -> tuple[Callable[[Any], bytes], Callable[[bytes], int]]:
	return (
		lambda value: int(value).to_bytes(length=length, byteorder=sys.byteorder, signed=False),
		lambda payload: int.from_bytes(payload, byteorder=sys.byteorder, signed=False),
	)


_ATTRIBUTE_BYTE_CODECS: tuple[tuple[str, Callable[[Any], bytes], Callable[[bytes], Any]], ...] = (
	("nvdaVersion", lambda value: str(value).encode(), lambda payload: payload.decode()),
	("rdAccessVersion", lambda value: str(value).encode(), lambda payload: payload.decode()),
	("protocolVersion", *_intCodec(1)),
	("timeSinceInput", *_intCodec(4)),
	("numCells", *_intCodec(1)),
	("numCols", *_intCodec(1)),
	("numRows", *_intCodec(1)),
)


def encodeAttributeValue(attribute: str, value: Any) -> bytes:
	for name, encode, _decode in _ATTRIBUTE_BYTE_CODECS:
		if attribute == name:
			return encode(value)
	return dumps(value)


def decodeAttributeValue(attribute: str, payload: bytes) -> Any:
	for name, _encode, decode in _ATTRIBUTE_BYTE_CODECS:
		if attribute == name:
			return decode(payload)
	return restrictedLoads(payload)


def encodeCommandPayload(
	driverType: DriverType,
	messageType: RdMessageType,
	payload: dict[str, Any],
) -> tuple[int, bytes]:
	"""Translate a value-based message into a legacy ``(command, payload)`` pair."""
	if messageType is RdMessageType.ATTRIBUTE_REQUEST:
		attribute: str = payload["attribute"]
		return (
			GenericCommand.ATTRIBUTE,
			ATTRIBUTE_SEPARATOR + attribute.encode("ASCII") + ATTRIBUTE_SEPARATOR,
		)
	if messageType is RdMessageType.ATTRIBUTE_VALUE:
		attribute = payload["attribute"]
		return (
			GenericCommand.ATTRIBUTE,
			ATTRIBUTE_SEPARATOR
			+ attribute.encode("ASCII")
			+ ATTRIBUTE_SEPARATOR
			+ encodeAttributeValue(attribute, payload["value"]),
		)
	command = _MESSAGE_TO_COMMAND[DriverType(driverType)].get(messageType)
	if command is None:
		raise ValueError(f"Message type {messageType!r} has no legacy command for {driverType!r}")
	encode, _decode = _PAYLOAD_CODECS[messageType]
	return (command, encode(payload))


def decodeCommandPayload(
	driverType: DriverType,
	command: int,
	payload: bytes,
) -> tuple[RdMessageType, dict[str, Any]]:
	"""Translate a legacy frame's command byte and payload into a value-based message."""
	if command == GenericCommand.ATTRIBUTE:
		attribute, rawValue = payload[1:].split(ATTRIBUTE_SEPARATOR, 1)
		name = attribute.decode("ASCII")
		if not rawValue:
			return (RdMessageType.ATTRIBUTE_REQUEST, {"attribute": name})
		return (
			RdMessageType.ATTRIBUTE_VALUE,
			{"attribute": name, "value": decodeAttributeValue(name, rawValue)},
		)
	messageType = _COMMAND_TO_MESSAGE[DriverType(driverType)].get(command)
	if messageType is None:
		raise ValueError(f"Command {command!r} unknown for {driverType!r}")
	_encode, decode = _PAYLOAD_CODECS[messageType]
	return (messageType, decode(payload))
