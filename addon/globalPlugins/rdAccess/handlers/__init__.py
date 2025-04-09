# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from ._remoteHandler import RemoteHandler
from .remoteBrailleHandler import RemoteBrailleHandler
from .remoteSpeechHandler import RemoteSpeechHandler

__all__ = [
	"RemoteBrailleHandler",
	"RemoteHandler",
	"RemoteSpeechHandler",
]
