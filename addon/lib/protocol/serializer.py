# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""JSON Lines serializer for protocol v2.

The wire format follows NVDA core's ``_remoteClient.serializer``: one UTF-8 encoded
JSON object per line with a mandatory ``type`` field. Speech sequences encode as
``[ClassName, __dict__]`` pairs, byte-for-byte identical to NVDA Remote Access;
conformance tests in ``tests/test_serializerConformance.py`` enforce this.

RDAccess-specific attribute values (driver settings, parameter infos, gesture maps,
speech command class sets) extend the same ``[ClassName, dict]`` convention and are
decoded against explicit per-attribute allowlists.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Callable
from fnmatch import fnmatchcase
from typing import Any

import inputCore
import speech.commands
from autoSettingsUtils.driverSetting import BooleanDriverSetting, DriverSetting, NumericDriverSetting
from autoSettingsUtils.utils import StringParameterInfo
from baseObject import AutoPropertyObject
from logHandler import log
from synthDriverHandler import VoiceInfo

from .braille import BrailleAttribute
from .messages import GenericAttribute, RdMessageType
from .speech import SpeechAttribute

JSONDict = dict[str, Any]

_SPEAK_TYPE = RdMessageType.SPEAK.value
_ATTRIBUTE_VALUE_TYPE = RdMessageType.ATTRIBUTE_VALUE.value

SEQUENCE_CLASSES = (
	speech.commands.SynthCommand,
	speech.commands.EndUtteranceCommand,
)

_SETTING_CLASSES: dict[str, type] = {
	cls.__name__: cls for cls in (DriverSetting, NumericDriverSetting, BooleanDriverSetting)
}
_PARAMETER_INFO_CLASSES: dict[str, type] = {cls.__name__: cls for cls in (StringParameterInfo, VoiceInfo)}


def _isSubclassOrInstance(unknown: Any, possible: type | tuple[type, ...]) -> bool:
	try:
		return issubclass(unknown, possible)
	except TypeError:
		return isinstance(unknown, possible)


class RdAccessJSONEncoder(json.JSONEncoder):
	def default(self, o: Any) -> Any:
		if _isSubclassOrInstance(o, SEQUENCE_CLASSES):
			return [o.__class__.__name__, o.__dict__]
		if isinstance(o, (DriverSetting, StringParameterInfo)):
			return [
				o.__class__.__name__,
				{k: v for k, v in o.__dict__.items() if k != "_propertyCache"},
			]
		if isinstance(o, inputCore.GlobalGestureMap):
			return [o.__class__.__name__, o.export()]
		if isinstance(o, type) and issubclass(o, speech.commands.SpeechCommand):
			return o.__name__
		if isinstance(o, (set, frozenset)) and all(isinstance(item, type) for item in o):
			return sorted(item.__name__ for item in o)
		return super().default(o)


def _reconstruct(allowedClasses: dict[str, type], item: Any) -> Any:
	if not isinstance(item, list) or len(item) != 2:
		raise ValueError(f"Expected a [className, state] pair, got {item!r}")
	name, state = item
	cls: Any = allowedClasses.get(name)
	if cls is None or not isinstance(state, dict):
		raise ValueError(f"Cannot reconstruct {name!r} from {state!r}")
	obj = cls.__new__(cls)
	obj.__dict__.update(state)
	if isinstance(obj, AutoPropertyObject):
		obj.invalidateCache()
	return obj


def _asSequence(dct: JSONDict) -> JSONDict:
	"""Object hook reconstructing speech commands in ``speak`` messages.

	Behavioral clone of ``_remoteClient.serializer.asSequence``: unknown or disallowed
	class names are logged and skipped, reconstruction bypasses ``__init__``.
	"""
	if not ("type" in dct and dct["type"] == _SPEAK_TYPE and "sequence" in dct):
		return dct
	sequence = []
	for item in dct["sequence"]:
		if not isinstance(item, list):
			sequence.append(item)
			continue
		name, values = item
		cls = getattr(speech.commands, name, None)
		if cls is None or not issubclass(cls, SEQUENCE_CLASSES):
			log.warning(f"Unknown sequence type received: {name!r}")
			continue
		cls = cls.__new__(cls)
		cls.__dict__.update(values)
		sequence.append(cls)
	dct["sequence"] = sequence
	return dct


def _decodeSupportedSettings(value: Any) -> list:
	if not isinstance(value, list):
		raise ValueError(f"Expected a list of settings, got {value!r}")
	return [_reconstruct(_SETTING_CLASSES, item) for item in value]


def _decodeAvailableValues(value: Any) -> OrderedDict:
	if not isinstance(value, dict):
		raise ValueError(f"Expected a mapping of parameter infos, got {value!r}")
	return OrderedDict((key, _reconstruct(_PARAMETER_INFO_CLASSES, item)) for key, item in value.items())


def _decodeSupportedCommands(value: Any) -> frozenset[type]:
	commands = set()
	for name in value:
		cls = getattr(speech.commands, name, None)
		if (
			cls is None
			or not isinstance(cls, type)
			or cls.__module__ != speech.commands.__name__
			or not issubclass(cls, speech.commands.SpeechCommand)
		):
			log.warning(f"Unknown speech command received: {name!r}")
			continue
		commands.add(cls)
	return frozenset(commands)


def _decodeGestureMap(value: Any) -> inputCore.GlobalGestureMap | None:
	if value is None:
		return None
	if not isinstance(value, list) or len(value) != 2 or value[0] != inputCore.GlobalGestureMap.__name__:
		raise ValueError(f"Cannot reconstruct a gesture map from {value!r}")
	gestureMap = inputCore.GlobalGestureMap()
	gestureMap.update(value[1])
	return gestureMap


ATTRIBUTE_DECODERS: tuple[tuple[str, Callable[[Any], Any]], ...] = (
	(GenericAttribute.SUPPORTED_SETTINGS, _decodeSupportedSettings),
	(SpeechAttribute.SUPPORTED_COMMANDS, _decodeSupportedCommands),
	(BrailleAttribute.GESTURE_MAP, _decodeGestureMap),
	("available*s", _decodeAvailableValues),
)


def decodeAttributeValue(attribute: str, value: Any) -> Any:
	for pattern, decoder in ATTRIBUTE_DECODERS:
		if fnmatchcase(attribute, pattern):
			return decoder(value)
	return value


_encoder = RdAccessJSONEncoder()
_decoder = json.JSONDecoder(object_hook=_asSequence)


class RdJSONSerializer:
	SEP: bytes = b"\n"

	def serialize(self, type: str | None = None, **obj: Any) -> bytes:
		obj["type"] = type
		return _encoder.encode(obj).encode("UTF-8") + self.SEP

	def deserialize(self, data: bytes) -> JSONDict:
		obj = _decoder.decode(data.decode("UTF-8"))
		if isinstance(obj, dict) and obj.get("type") == _ATTRIBUTE_VALUE_TYPE:
			obj["value"] = decodeAttributeValue(obj.get("attribute", ""), obj.get("value"))
		return obj
