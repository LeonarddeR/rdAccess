# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2026 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

"""Unit test package bootstrap.

Importing this package prepares an environment in which ``addon/lib/protocol``
can be imported without a running NVDA instance:

* ``addon`` is put on ``sys.path`` so the protocol package resolves as ``lib.protocol``.
* The sibling NVDA source checkout (``../nvda/source``) is put on ``sys.path`` so the
  real ``baseObject`` and ``extensionPoints`` modules are used.
* Light-weight stand-ins for NVDA runtime modules are installed into ``sys.modules``
  (see :mod:`tests._stubs`) before anything imports them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_NVDA_SOURCE = (_REPO_ROOT.parent / "nvda" / "source").resolve()
if not (_NVDA_SOURCE / "baseObject.py").is_file():
	raise RuntimeError(
		"The unit tests require an NVDA source checkout in a directory next to this repository. "
		f"Expected to find {_NVDA_SOURCE / 'baseObject.py'}. "
		"Clone https://github.com/nvaccess/nvda.git as a sibling of this repository.",
	)
sys.path.insert(0, str(_NVDA_SOURCE))
sys.path.insert(0, str(_REPO_ROOT / "addon"))

from . import _stubs  # noqa: E402

_stubs.install()
