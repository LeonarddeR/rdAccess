from ._remoteHandler import RemoteHandler
import braille
from hwIo import intToByte
import typing

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleHandler(RemoteHandler):

	def __init__(self, pipeAddress: str):
		super().__init__(protocol.DriverType.BRAILLE, pipeAddress)
		self._sendNumCells()
		self._sendGestureMap()

	_currentDisplay: braille.BrailleDisplayDriver

	def _get__currentDisplay(self):
		return braille.handler.display

	@protocol.attributeSender(protocol.BrailleAttribute.NUM_CELLS)
	def _sendNumCells(self) -> bytes:
		return intToByte(self._currentDisplay.numCells)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _sendGestureMap(self) -> bytes:
		return self.pickle(self._currentDisplay.gestureMap)

	@protocol.commandHandler(protocol.BrailleCommand.DISPLAY)
	def _handleDisplay(self, payload: bytes):
		cells = list(payload)
		if braille.handler.displaySize > 0:
			# We use braille.handler._writeCells since this respects thread safe displays
			# and automatically falls back to noBraille if desired
			braille.handler._writeCells(cells)
