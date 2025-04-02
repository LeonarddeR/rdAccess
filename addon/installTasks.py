# RDAccess: Remote Desktop Accessibility for NVDA
# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import typing
from time import sleep

import addonHandler

if typing.TYPE_CHECKING:
	from .lib import configuration, rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	rdPipe = addon.loadModule("lib.rdPipe")


def onInstall():
	configuration.initializeConfig()


def onUninstall():
	for architecture in set((rdPipe.DEFAULT_ARCHITECTURE, rdPipe.Architecture.X86)):
		rdPipe.dllInstall(
			install=False,
			comServer=True,
			rdp=True,
			citrix=architecture == rdPipe.Architecture.X86,
			architecture=architecture,
		)
	# Sleep for a second to ensure we can delete the directory.
	sleep(1.0)
