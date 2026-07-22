# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

"""Loads NVDA core's Remote Access protocol modules from the sibling NVDA source checkout.

``_remoteClient/__init__.py`` pulls in wx and NVDA config, so ``serializer.py`` and
``protocol.py`` are loaded directly by file path, outside their package. Their imports
(``speech.commands``, ``logHandler``) resolve against the stubs installed by :mod:`tests._stubs`.

Conformance tests compare RDAccess's serializer output against these modules, so they fail
as soon as the NVDA Remote wire protocol drifts.
"""

from __future__ import annotations

import importlib.util
import sys
from types import ModuleType

from . import _NVDA_SOURCE

_REMOTE_CLIENT_DIR = _NVDA_SOURCE / "_remoteClient"


def _loadModule(fileName: str, moduleName: str) -> ModuleType:
	if moduleName in sys.modules:
		return sys.modules[moduleName]
	path = _REMOTE_CLIENT_DIR / fileName
	if not path.is_file():
		raise RuntimeError(f"Expected NVDA Remote Access module at {path}")
	spec = importlib.util.spec_from_file_location(moduleName, path)
	assert spec is not None and spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	sys.modules[moduleName] = module
	spec.loader.exec_module(module)
	return module


protocol = _loadModule("protocol.py", "_nvdaRemoteProtocol")
serializer = _loadModule("serializer.py", "_nvdaRemoteSerializer")
