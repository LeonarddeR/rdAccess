from ._remoteHandler import RemoteHandler
import typing

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib\\protocol")


class RemoteSpeechHandler(RemoteHandler):

	def __init__(self, pipeAddress: str):
		super().__init__(protocol.DriverType.SPEECH, pipeAddress)
