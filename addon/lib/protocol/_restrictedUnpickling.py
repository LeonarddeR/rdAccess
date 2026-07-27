# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023-2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later
"""Allowlist-restricted unpickling for payloads received over the RDAccess wire.

``pickle.loads`` on untrusted data is an arbitrary-code-execution primitive, and RDAccess
deserializes payloads that arrive over the DVC named pipe from a peer across the RDP trust
boundary. This module confines unpickling to an allowlist of the classes that legitimately
cross the wire, blocking the generic ``__reduce__``-based gadget class (``os.system``,
``builtins.eval``, ``subprocess.*``, etc.) while staying wire-compatible with existing peers.
"""

from __future__ import annotations

import io
import pickle
from typing import Any

from logHandler import log

_allowedUnpickleGlobals: dict[tuple[str, str], type] | None = None


def _getAllowedGlobals() -> dict[tuple[str, str], type]:
	"""Return the allowlist of classes RestrictedUnpickler may resolve, keyed by
	``(cls.__module__, cls.__qualname__)``.

	The classes are imported lazily (only on first call, then cached) rather than at module import
	time, so that import order of NVDA's internal modules is unaffected and unit tests can stub the
	modules before this is ever invoked. Keys are built from the imported class objects themselves
	(not hardcoded strings) so they always match whatever string the pickling side actually wrote,
	which matters in particular for RDAccess's own BrailleInputGesture: its __module__ is whatever
	addonHandler.Addon.loadModule names the add-on module as, identical on both sides of the wire.
	"""
	global _allowedUnpickleGlobals
	if _allowedUnpickleGlobals is None:
		from collections import OrderedDict

		from autoSettingsUtils.driverSetting import (
			BooleanDriverSetting,
			DriverSetting,
			NumericDriverSetting,
		)
		from autoSettingsUtils.utils import StringParameterInfo
		from inputCore import GlobalGestureMap
		from synthDriverHandler import VoiceInfo

		from .braille import BrailleInputGesture

		classes: tuple[type, ...] = (
			DriverSetting,
			NumericDriverSetting,
			BooleanDriverSetting,
			StringParameterInfo,
			VoiceInfo,
			GlobalGestureMap,
			OrderedDict,
			BrailleInputGesture,
		)
		allowedGlobals: dict[tuple[str, str], type] = {
			(str(cls.__module__), str(cls.__qualname__)): cls for cls in classes
		}
		# Compat alias: peers on older NVDA pickled this under its pre-move module name.
		allowedGlobals[("driverHandler", "StringParameterInfo")] = StringParameterInfo
		_allowedUnpickleGlobals = allowedGlobals
	return _allowedUnpickleGlobals


class RestrictedUnpickler(pickle.Unpickler):
	"""Restricts unpickling to an allowlist of classes that legitimately cross the RDAccess wire.

	pickle.loads on untrusted data is an arbitrary-code-execution primitive: a crafted payload's
	__reduce__ can reference any importable global (os.system, builtins.eval, subprocess.*, etc.).
	Overriding find_class so it only ever resolves allowlisted classes blocks that gadget class
	entirely, while remaining wire-compatible with existing RDAccess peers (builtin containers and
	scalars never go through find_class; only global/class lookups do).
	"""

	def find_class(self, module: str, name: str) -> Any:
		if module == "speech.commands":
			# Speech command classes are allowed dynamically so future NVDA-added commands work
			# without an add-on update, while anything else in the module is still refused.
			import speech.commands

			obj = getattr(speech.commands, name, None)
			if (
				isinstance(obj, type)
				and obj.__module__ == module
				and issubclass(obj, speech.commands.SpeechCommand)
			):
				return obj
		else:
			cls = _getAllowedGlobals().get((module, name))
			if cls is not None:
				return cls
		log.error(f"Refusing to unpickle disallowed global: module={module!r}, name={name!r}")
		raise pickle.UnpicklingError(f"Global '{module}.{name}' is forbidden")


def restrictedLoads(payload: bytes) -> Any:
	"""Unpickle ``payload`` through RestrictedUnpickler's allowlist."""
	return RestrictedUnpickler(io.BytesIO(payload)).load()
