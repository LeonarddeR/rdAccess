import addonHandler
import gui
import wx
import typing

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


addonHandler.initTranslation()


def onInstall():
	...
