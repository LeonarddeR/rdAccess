# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Stand-ins for NVDA runtime modules, installed into ``sys.modules``.

Only leaf modules are stubbed. ``baseObject``, ``extensionPoints``, ``winKernel``, the
``hwIo`` submodules, ``speech.commands`` and ``braille.constants`` are imported for real from the
sibling NVDA source checkout; their dependencies (``logHandler``, ``garbageHandler``, ``NVDAState``,
``config``, ``synthDriverHandler.getSynth``) are covered here, as is the ``_`` gettext builtin that
NVDA installs at startup. ``winUser`` and ``keyboardHandler`` expose just what ``lib.capsLock``
reads: the caps lock virtual key code, the ``ignoreInjected`` flag and ``isNVDAModifierKey``,
which treats caps lock as the NVDA modifier key.
"""

from __future__ import annotations

import gettext
import importlib
import sys
import types
from pathlib import Path
from typing import Any

_NVDA_SOURCE = Path(__file__).resolve().parent.parent.parent / "nvda" / "source"


class FakeLogger:
	"""Collects log records so tests can optionally assert on them."""

	DEBUG = 10
	INFO = 20

	def __init__(self):
		self.records: list[tuple[str, str]] = []

	def isEnabledFor(self, level: int) -> bool:
		return False

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

	# Binds `_` into builtins, which modules imported from the NVDA checkout expect.
	gettext.NullTranslations().install()

	logHandler = _module("logHandler")
	logHandler.log = FakeLogger()

	def getFormattedStacksForAllThreads() -> str:
		return ""

	logHandler.getFormattedStacksForAllThreads = getFormattedStacksForAllThreads

	config = _module("config")
	config.conf = {
		"debugLog": {"hwIo": False, "speechManager": False},
		"featureFlag": {"cancelExpiredFocusSpeech": 0},
	}

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

	_installHwIo()

	buildVersion = _module("buildVersion")
	buildVersion.version_year = 2026
	buildVersion.version_major = 3

	_installBraille()

	speech = _module("speech")
	_installDriverSettingAndSynthVoiceStubs()
	_installSpeechCommands(speech)
	_installInputCoreStub()
	_installKeyboardStubs()


def _installHwIo() -> None:
	"""Make the real ``hwIo.base`` and ``hwIo.ioThread`` importable.

	``hwIo/__init__.py`` pulls in ``comtypes`` via ``hwIo.hid``, which is not a dev dependency,
	so ``hwIo`` is registered as a module whose ``__path__`` points straight at the package
	directory. Submodule imports then resolve against the real sources without that import
	ever running.
	"""
	hwIo = _module("hwIo")
	hwIo.__path__ = [str(_NVDA_SOURCE / "hwIo")]
	hwIo.base = importlib.import_module("hwIo.base")
	hwIo.ioThread = importlib.import_module("hwIo.ioThread")


def _installBraille() -> None:
	"""Cover the ``braille`` symbols that ``nvdaCompat`` reaches for on either side of NVDA 2026.3.

	Like ``hwIo``, the ``braille`` package is registered with ``__path__`` pointing straight at the
	real sources, so ``braille.constants`` (which imports nothing but ``typing``) resolves against
	the NVDA checkout without ``braille/__init__.py`` ever running. The remaining submodules are
	pre-registered as stubs, both because they bottom out in ``inputCore.InputGesture`` and
	``bdDetect``, and so that the import above cannot pull them in. The same objects are also
	exposed under the pre-2026.3 names (the ``braille`` facade and the ``brailleInput`` module),
	so ``nvdaCompat`` can be reloaded as an older NVDA would import it.
	"""
	braille = _module("braille")
	braille.__path__ = [str(_NVDA_SOURCE / "braille")]
	brailleDisplay = _module("braille.display")
	braille.display = brailleDisplay
	brailleDisplayGesture = _module("braille.display.gesture")
	brailleDisplay.gesture = brailleDisplayGesture
	brailleDisplayDriver = _module("braille.display.driver")
	brailleDisplay.driver = brailleDisplayDriver
	brailleExtensions = _module("braille.extensions")
	braille.extensions = brailleExtensions
	brailleInput = _module("braille.input")
	braille.input = brailleInput
	brailleInputGesture = _module("braille.input.gesture")
	brailleInput.gesture = brailleInputGesture

	braille.constants = importlib.import_module("braille.constants")

	class BrailleDisplayGesture:
		cellIndexes: list[int] | None = None

		@property
		def routingIndex(self) -> int | None:
			return max(self.cellIndexes) if self.cellIndexes else None

		@routingIndex.setter
		def routingIndex(self, value: int | None) -> None:
			self.cellIndexes = [value] if value is not None else None

	brailleDisplayGesture.BrailleDisplayGesture = BrailleDisplayGesture

	class BrailleDisplayDriver:
		pass

	brailleDisplayDriver.BrailleDisplayDriver = BrailleDisplayDriver

	brailleExtensions.decide_enabled = object()
	brailleExtensions.displayChanged = object()

	class BrailleInputGesture:
		pass

	brailleInputGesture.BrailleInputGesture = BrailleInputGesture

	braille.AUTOMATIC_PORT = braille.constants.AUTOMATIC_PORT
	braille.BrailleDisplayDriver = BrailleDisplayDriver
	braille.BrailleDisplayGesture = BrailleDisplayGesture
	braille.decide_enabled = brailleExtensions.decide_enabled
	braille.displayChanged = brailleExtensions.displayChanged
	brailleInput = _module("brailleInput")
	brailleInput.BrailleInputGesture = BrailleInputGesture


def _setStubIdentity(cls: type, module: str) -> None:
	"""Set __module__ and __qualname__ on a class defined inside a function.

	Classes defined here get __module__ == "tests._stubs" and __qualname__ containing
	"install.<locals>." (or similar) by default; both must be corrected so pickled payloads in
	tests carry the same module/qualname strings as real NVDA would produce. Pickle refuses to
	pickle-by-reference a class whose __qualname__ contains "<locals>".
	"""
	cls.__module__ = module
	cls.__qualname__ = cls.__name__


def _installSpeechCommands(speech: types.ModuleType) -> None:
	"""Make the real ``speech.commands`` (and ``speech.manager`` and its dependencies) importable
	from the NVDA checkout.

	``speech/__init__.py`` pulls in the full speech subsystem, so like ``hwIo`` the package is
	registered with ``__path__`` pointing straight at the real sources. ``speech.commands``
	itself only needs ``config`` and ``synthDriverHandler.getSynth``, both installed above.
	``speech.languageHandling`` pulls in the full ``speech.speech`` module, so the one function
	``speech.manager`` needs from it is stubbed instead.
	"""
	speech.__path__ = [str(_NVDA_SOURCE / "speech")]
	speechCommands = importlib.import_module("speech.commands")
	speech.commands = speechCommands

	class NotASpeechCommand:
		"""Injected into speech.commands without being a SpeechCommand subclass; used to test
		that the dynamic find_class rule for speech.commands rejects it.
		"""

	_setStubIdentity(NotASpeechCommand, "speech.commands")
	speechCommands.NotASpeechCommand = NotASpeechCommand

	speechLanguageHandling = _module("speech.languageHandling")

	def shouldSwitchVoice() -> bool:
		return True

	speechLanguageHandling.shouldSwitchVoice = shouldSwitchVoice
	speech.languageHandling = speechLanguageHandling


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

	from extensionPoints import Action

	synthDriverHandler = _module("synthDriverHandler")
	synthDriverHandler._currentSynth = None

	def getSynth() -> Any:
		return synthDriverHandler._currentSynth

	synthDriverHandler.getSynth = getSynth
	synthDriverHandler.synthIndexReached = Action()
	synthDriverHandler.synthDoneSpeaking = Action()
	synthDriverHandler.pre_synthSpeak = Action()

	class SynthDriver:
		pass

	_setStubIdentity(SynthDriver, "synthDriverHandler")
	synthDriverHandler.SynthDriver = SynthDriver

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

		def export(self) -> dict:
			return {section: dict(scripts) for section, scripts in self._map.items()}

	_setStubIdentity(GlobalGestureMap, "inputCore")
	inputCore.GlobalGestureMap = GlobalGestureMap


def _installKeyboardStubs() -> None:
	winUser = _module("winUser")
	winUser.VK_CAPITAL = 0x14

	keyboardHandler = _module("keyboardHandler")
	keyboardHandler.ignoreInjected = False

	def isNVDAModifierKey(vkCode: int, _extended: bool) -> bool:
		return vkCode == winUser.VK_CAPITAL

	keyboardHandler.isNVDAModifierKey = isNVDAModifierKey
