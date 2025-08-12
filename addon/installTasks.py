# RDAccess: Remote Desktop Accessibility for NVDA
# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import subprocess
import typing
from time import sleep

import addonHandler
from logHandler import log

if typing.TYPE_CHECKING:
	from .lib import configuration, rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	rdPipe = addon.loadModule("lib.rdPipe")


def onInstall():
	configuration.initializeConfig()


def onUninstall():
	for architecture in {rdPipe.defaultArchitecture, rdPipe.Architecture.X86}:
		try:
			rdPipe.dllInstall(
				install=False,
				comServer=True,
				rdp=True,
				citrix=architecture == rdPipe.Architecture.X86,
				architecture=architecture,
			)
		except subprocess.CalledProcessError:
			log.debugWarning(f"Failed to uninstall RD Pipe for architecture: {architecture}", exc_info=True)
	# Sleep for a second to ensure we can delete the directory.
	sleep(1.0)
