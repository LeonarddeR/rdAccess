import typing
from time import sleep

if typing.TYPE_CHECKING:
	from .lib import configuration
	from .lib import rdPipe
else:
	import addonHandler
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
			architecture=architecture
		)
	# Sleep for a second to ensure we can delete the directory.
	sleep(1.0)
