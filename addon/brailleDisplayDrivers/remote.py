import braille
import typing
import addonHandler
from typing import List
from inputCore import GlobalGestureMap

if typing.TYPE_CHECKING:
	from ..lib import driver
	from ..lib import protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleDisplayDriver(driver.WTSRemoteDriver, braille.BrailleDisplayDriver):
	name = "remote"
	# Translators: Name for a remote braille display.
	description = _("Remote Braille")
	isThreadSafe = True

	def _handleRemoteDisconnect(self):
		# Raise an exception because handleDisplayUnavailable expects one
		try:
			raise RuntimeError("XOFF received, remote client disconnected")
		except RuntimeError:
			braille.handler.handleDisplayUnavailable()

	def __init__(self, port="auto"):
		braille.BrailleDisplayDriver.__init__(self, port)
		driver.WTSRemoteDriver.__init__(self, protocol.DriverType.BRAILLE)

	@protocol.attributeHandler(protocol.BrailleAttribute.NUM_CELLS, defaultValue=0)
	def _handleNumCellsUpdate(self, payload: bytes):
		if len(payload) == 0:
			return 0
		assert len(payload) == 1
		return ord(payload)

	def _get_numCells(self) -> int:
		return self._attributeHandlers[protocol.BrailleAttribute.NUM_CELLS].value

	@protocol.attributeHandler(protocol.BrailleAttribute.GESTURE_MAP, defaultValue=GlobalGestureMap())
	def _handleGestureMapUpdate(self, payload: bytes):
		assert len(payload) > 0
		return self.unpickle(payload)

	def _get_gestureMap(self) -> GlobalGestureMap:
		return self._attributeHandlers[protocol.BrailleAttribute.GESTURE_MAP].value

	def display(self, cells: List[int]):
		# cells will already be padded up to numCells.
		arg = bytes(cells)
		self.writeMessage(protocol.BrailleCommand.DISPLAY, arg)


BrailleDisplayDriver = RemoteBrailleDisplayDriver
