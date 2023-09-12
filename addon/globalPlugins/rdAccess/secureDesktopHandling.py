# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from __future__ import annotations
from .handlers import RemoteBrailleHandler, RemoteSpeechHandler
from .handlers._remoteHandler import RemoteHandler
import typing
from baseObject import AutoPropertyObject
import addonHandler
import os.path
import braille
import synthDriverHandler
import weakref

if typing.TYPE_CHECKING:
    from ...lib import ioThreadEx
    from ...lib import namedPipe
else:
    addon: addonHandler.Addon = addonHandler.getCodeAddon()
    ioThreadEx = addon.loadModule("lib.ioThreadEx")
    namedPipe = addon.loadModule("lib.namedPipe")


HandlerTypeT = typing.TypeVar("HandlerTypeT", bound=RemoteHandler)


class SecureDesktopHandler(AutoPropertyObject):
    _ioThreadRef: weakref.ReferenceType[ioThreadEx.IoThreadEx]
    _brailleHandler: RemoteBrailleHandler
    _speechHandler: RemoteSpeechHandler

    def __init__(self, ioThread: ioThreadEx.IoThreadEx):
        self._ioThreadRef = weakref.ref(ioThread)
        braille.handler.display.saveSettings()
        self._brailleHandler = self._initializeHandler(RemoteBrailleHandler)
        synthDriverHandler.getSynth().saveSettings()
        self._speechHandler = self._initializeHandler(RemoteSpeechHandler)

    def terminate(self):
        self._speechHandler.terminate()
        braille.handler.display.loadSettings()
        self._brailleHandler.terminate()
        synthDriverHandler.getSynth().loadSettings()

    def _initializeHandler(
        self, handlerType: typing.Type[HandlerTypeT]
    ) -> HandlerTypeT:
        sdId = f"NVDA_SD-{handlerType.driverType.name}"
        sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
        handler = handlerType(self._ioThreadRef(), sdPort, False)
        return handler
