# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import subprocess
import typing
from time import sleep

import addonHandler
from logHandler import log


def onUninstall():
	if typing.TYPE_CHECKING:
		from .lib import rdPipe
	else:
		addon: addonHandler.Addon = addonHandler.getCodeAddon()
		rdPipe = addon.loadModule("lib.rdPipe")
	for architecture in {rdPipe.defaultArchitecture, rdPipe.Architecture.X86}:
		try:
			rdPipe.dllInstall(
				install=False,
				comServer=True,
				rdp=True,
				citrix=architecture == rdPipe.Architecture.X86 and rdPipe.isCitrixSupported(),
				architecture=architecture,
			)
		except subprocess.CalledProcessError:
			log.debugWarning(f"Failed to uninstall RD Pipe for architecture: {architecture}", exc_info=True)
	# Sleep for a second to ensure we can delete the directory.
	sleep(1.0)
