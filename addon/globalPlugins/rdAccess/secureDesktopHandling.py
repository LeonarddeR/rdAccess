# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from __future__ import annotations

import os.path
import typing
import weakref

import addonHandler
import braille
import installer
import synthDriverHandler
from baseObject import AutoPropertyObject
from logHandler import log

from .handlers import RemoteBrailleHandler, RemoteSpeechHandler
from .handlers._remoteHandler import RemoteHandler

addon: addonHandler.Addon = addonHandler.getCodeAddon()
if typing.TYPE_CHECKING:
	from ...lib import ioThreadEx, namedPipe
else:
	ioThreadEx = addon.loadModule("lib.ioThreadEx")
	namedPipe = addon.loadModule("lib.namedPipe")


HandlerTypeT = typing.TypeVar("HandlerTypeT", bound=RemoteHandler)


class SecureDesktopHandler(AutoPropertyObject):
	_ioThreadRef: weakref.ReferenceType[ioThreadEx.IoThreadEx]
	_brailleHandler: RemoteBrailleHandler
	_speechHandler: RemoteSpeechHandler

	def __init__(self, ioThread: ioThreadEx.IoThreadEx):
		log.info("Initializing RDAccess secure desktop handling")
		self._ioThreadRef = weakref.ref(ioThread)
		braille.handler.display.saveSettings()
		self._brailleHandler = self._initializeHandler(RemoteBrailleHandler)
		synthDriverHandler.getSynth().saveSettings()
		self._speechHandler = self._initializeHandler(RemoteSpeechHandler)

	def terminate(self):
		log.info("Terminating RDAccess secure desktop handling")
		self._speechHandler.terminate()
		braille.handler.display.loadSettings()
		self._brailleHandler.terminate()
		synthDriverHandler.getSynth().loadSettings()

	def _initializeHandler(self, handlerType: type[HandlerTypeT]) -> HandlerTypeT:
		sdId = f"NVDA_SD-{handlerType.driverType.name}"
		sdPort = os.path.join(namedPipe.PIPE_DIRECTORY, sdId)
		handler = handlerType(self._ioThreadRef(), sdPort, False)
		return handler


def isAddonAvailableInSystemConfig() -> bool:
	"""Check if the addon is available in the system configuration."""
	addonPath = os.path.join(installer.getInstallPath(), "systemConfig", "addons", addon.name)
	try:
		addonHandler.Addon(addonPath)
	except Exception:
		log.debugWarning(f"Couldn't load addon from path: {addonPath!r}", exc_info=True)
		return False
	return True
