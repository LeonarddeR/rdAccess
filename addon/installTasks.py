import addonHandler
import gui
import wx
impor ttyping

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


addonHandler.initTranslation()


def onInstall():
	...
