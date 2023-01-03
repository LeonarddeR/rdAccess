import typing
import addonHandler

if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


class RemoteHandler(protocol.RemoteProtocolHandler):

	def __init__(self, driverType: protocol.DriverType, pipeAddress: str):
		super().__init__(driverType)
		try:
			self._dev = namedPipe.NamedPipe(pipeAddress, onReceive=self._onReceive)
		except EnvironmentError:
			raise

	def terminate(self):
		# Make sure the device gets closed.
		self._dev.close()
