# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import typing
from time import sleep
import addonHandler
import gui
import wx

if typing.TYPE_CHECKING:
	from .lib import configuration
	from .lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	rdPipe = addon.loadModule("lib.rdPipe")


def onInstall():
	for addon in addonHandler.getAvailableAddons():
		if addon.name == "nvdaRd":
			result = gui.messageBox(
				# Translators: message asking the user to remove nvdaRd add-on
				_(
					"This add-on was previously called NVDA Remote Desktop. "
					"You have an installed version of that add-on. "
					"Would you like to update to RDAccess?"
				),
				# Translators: question title
				_("Previous version detected"),
				wx.YES_NO | wx.ICON_WARNING
			)
			if result == wx.YES:
				addon.requestRemove()
			else:
				raise addonHandler.AddonError("Installed nvdaRd found that needs to be removed first")
	configuration.initializeConfig()


def onUninstall():
	for architecture in set((rdPipe.DEFAULT_ARCHITECTURE, rdPipe.Architecture.X86)):
		rdPipe.dllInstall(
			install=False,
			comServer=True,
			rdp=True,
			citrix=architecture == rdPipe.Architecture.X86,
			architecture=architecture
		)
	# Sleep for a second to ensure we can delete the directory.
	sleep(1.0)
