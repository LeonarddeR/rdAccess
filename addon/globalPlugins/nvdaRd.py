import globalPluginHandler
import addonHandler
import hwIo

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super().__init__()
		addon = addonHandler.getCodeAddon()
		addon.loadModule("lib")
