# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Stand-ins for NVDA runtime modules, installed into ``sys.modules``.

Only leaf modules are stubbed. ``baseObject`` and ``extensionPoints`` are imported
for real from the sibling NVDA source checkout; their dependencies (``logHandler``,
``garbageHandler``, ``NVDAState``) are covered here.
"""

from __future__ import annotations

import sys
import types
from typing import Any


class FakeLogger:
	"""Collects log records so tests can optionally assert on them."""

	def __init__(self):
		self.records: list[tuple[str, str]] = []

	def _log(self, level: str, msg: Any, *args: Any, **kwargs: Any):
		self.records.append((level, str(msg)))

	def debug(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("debug", msg)

	def debugWarning(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("debugWarning", msg)

	def info(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("info", msg)

	def warning(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("warning", msg)

	def error(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("error", msg)

	def exception(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("exception", msg)

	def critical(self, msg: Any, *args: Any, **kwargs: Any):
		self._log("critical", msg)


def _module(name: str) -> types.ModuleType:
	mod = types.ModuleType(name)
	sys.modules[name] = mod
	return mod


def install():
	"""Install all stub modules. Idempotent; must run before importing ``lib.protocol``."""
	if "logHandler" in sys.modules:
		return

	logHandler = _module("logHandler")
	logHandler.log = FakeLogger()

	garbageHandler = _module("garbageHandler")

	class TrackedObject:
		"""Unlike the real one, defines no __del__, keeping garbage collection in tests silent."""

	garbageHandler.TrackedObject = TrackedObject

	NVDAState = _module("NVDAState")

	def _allowDeprecatedAPI() -> bool:
		return False

	NVDAState._allowDeprecatedAPI = _allowDeprecatedAPI

	addonHandler = _module("addonHandler")

	class Addon:
		version = "0.0-test"
		name = "rdAccessTest"

	def getCodeAddon() -> Addon:
		return Addon()

	addonHandler.Addon = Addon
	addonHandler.getCodeAddon = getCodeAddon

	queueHandler = _module("queueHandler")
	queueHandler.eventQueue = object()
	queuedFunctions: list[tuple[Any, Any, tuple, dict]] = []

	def queueFunction(queue: Any, func: Any, *args: Any, **kwargs: Any):
		queuedFunctions.append((queue, func, args, kwargs))

	def pumpAll():
		"""Execute and drain everything queued through queueFunction."""
		while queuedFunctions:
			_queue, func, args, kwargs = queuedFunctions.pop(0)
			func(*args, **kwargs)

	queueHandler.queuedFunctions = queuedFunctions
	queueHandler.queueFunction = queueFunction
	queueHandler.pumpAll = pumpAll

	versionInfo = _module("versionInfo")
	versionInfo.version_detailed = "2026.1.0-test"

	hwIo = _module("hwIo")
	hwIoBase = _module("hwIo.base")
	hwIo.base = hwIoBase

	class IoBase:
		def write(self, data: bytes):
			raise NotImplementedError

		def waitForRead(self, timeout: float) -> bool:
			raise NotImplementedError

		def close(self):
			pass

	hwIoBase.IoBase = IoBase

	braille = _module("braille")

	class BrailleDisplayGesture:
		pass

	braille.BrailleDisplayGesture = BrailleDisplayGesture

	brailleInput = _module("brailleInput")

	class BrailleInputGesture:
		pass

	brailleInput.BrailleInputGesture = BrailleInputGesture

	speech = _module("speech")
	speechManager = _module("speech.manager")
	speech.manager = speechManager

	class SpeechManager:
		MAX_INDEX = 9999

	speechManager.SpeechManager = SpeechManager

	_installSpeechCommandsStub(speech)
	_installDriverSettingAndSynthVoiceStubs()
	_installInputCoreStub()


def _setStubIdentity(cls: type, module: str) -> None:
	"""Set __module__ and __qualname__ on a class defined inside a function.

	Classes defined here get __module__ == "tests._stubs" and __qualname__ containing
	"install.<locals>." (or similar) by default; both must be corrected so pickled payloads in
	tests carry the same module/qualname strings as real NVDA would produce. Pickle refuses to
	pickle-by-reference a class whose __qualname__ contains "<locals>".
	"""
	cls.__module__ = module
	cls.__qualname__ = cls.__name__


def _installSpeechCommandsStub(speech: types.ModuleType) -> None:
	speechCommands = _module("speech.commands")
	speech.commands = speechCommands

	class SpeechCommand:
		pass

	class IndexCommand(SpeechCommand):
		def __init__(self, index: int):
			self.index = index

		def __eq__(self, other: Any) -> bool:
			return type(self) is type(other) and self.index == other.index

	class PitchCommand(SpeechCommand):
		def __init__(self, offset: int = 0):
			self.offset = offset

		def __eq__(self, other: Any) -> bool:
			return type(self) is type(other) and self.offset == other.offset

	class NotASpeechCommand:
		"""Exists in speech.commands but is not a SpeechCommand subclass; used to test that the
		dynamic find_class rule for speech.commands rejects it.
		"""

	for cls in (SpeechCommand, IndexCommand, PitchCommand, NotASpeechCommand):
		_setStubIdentity(cls, "speech.commands")

	speechCommands.SpeechCommand = SpeechCommand
	speechCommands.IndexCommand = IndexCommand
	speechCommands.PitchCommand = PitchCommand
	speechCommands.NotASpeechCommand = NotASpeechCommand


def _installDriverSettingAndSynthVoiceStubs() -> None:
	from baseObject import AutoPropertyObject

	autoSettingsUtils = _module("autoSettingsUtils")
	autoSettingsDriverSetting = _module("autoSettingsUtils.driverSetting")
	autoSettingsUtils.driverSetting = autoSettingsDriverSetting
	autoSettingsUtilsUtils = _module("autoSettingsUtils.utils")
	autoSettingsUtils.utils = autoSettingsUtilsUtils

	class StringParameterInfo:
		def __init__(self, id: str, displayName: str):
			self.id = id
			self.displayName = displayName

		def __eq__(self, other: Any) -> bool:
			return type(self) is type(other) and self.id == other.id and self.displayName == other.displayName

	class DriverSetting(AutoPropertyObject):
		def __init__(
			self,
			id: str,
			displayNameWithAccelerator: str,
			availableInSettingsRing: bool = False,
			defaultVal: Any = None,
			displayName: str | None = None,
			useConfig: bool = True,
		):
			self.id = id
			self.displayNameWithAccelerator = displayNameWithAccelerator
			self.displayName = displayName or displayNameWithAccelerator
			self.availableInSettingsRing = availableInSettingsRing
			self.defaultVal = defaultVal
			self.useConfig = useConfig

	class NumericDriverSetting(DriverSetting):
		pass

	class BooleanDriverSetting(DriverSetting):
		pass

	_setStubIdentity(StringParameterInfo, "autoSettingsUtils.utils")
	for cls in (DriverSetting, NumericDriverSetting, BooleanDriverSetting):
		_setStubIdentity(cls, "autoSettingsUtils.driverSetting")

	autoSettingsUtilsUtils.StringParameterInfo = StringParameterInfo
	autoSettingsDriverSetting.DriverSetting = DriverSetting
	autoSettingsDriverSetting.NumericDriverSetting = NumericDriverSetting
	autoSettingsDriverSetting.BooleanDriverSetting = BooleanDriverSetting

	synthDriverHandler = _module("synthDriverHandler")

	class VoiceInfo(StringParameterInfo):
		def __init__(self, id: str, displayName: str, language: str | None = None):
			self.language = language
			super().__init__(id, displayName)

	_setStubIdentity(VoiceInfo, "synthDriverHandler")
	synthDriverHandler.VoiceInfo = VoiceInfo


def _installInputCoreStub() -> None:
	inputCore = _module("inputCore")

	class GlobalGestureMap:
		def __init__(self, entries: Any = None):
			self._map: dict = {}
			self.lastUpdateContainedError = False
			self.fileName: str | None = None
			if entries:
				self.update(entries)

		def update(self, entries: Any):
			self._map.update(entries)

	_setStubIdentity(GlobalGestureMap, "inputCore")
	inputCore.GlobalGestureMap = GlobalGestureMap
