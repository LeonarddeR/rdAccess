import typing

if typing.TYPE_CHECKING:
	from .lib import rdPipe
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	rdPipe = addon.loadModule("lib.rdPipe")


def onUninstall():
	for architecture in set((rdPipe.DEFAULT_ARCHITECTURE, rdPipe.Architecture.X86)):
		rdPipe.dllInstall(
			install=False,
			comServer=True,
			rdp=True,
			citrix=architecture == rdPipe.Architecture.X86,
			architecture=architecture
		)
