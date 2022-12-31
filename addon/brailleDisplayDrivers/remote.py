import braille
import typing
import addonHandler
from typing import List

if typing.TYPE_CHECKING:
	from ..lib import driver
	from ..lib import protocol
	from ..lib import wtsVirtualChannel
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib\\driver")
	protocol = addon.loadModule("lib\\protocol")
	wtsVirtualChannel = addon.loadModule("lib\\wtsVirtualChannel")


class RemoteBrailleDisplayDriver(braille.BrailleDisplayDriver, driver.RemoteDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote Braille")
	isThreadSafe = True

	check = driver.RemoteDriver.check

	@protocol.attributeHandler(protocol.BrailleAttribute.NUM_CELLS)
	def _handleNumCellsUpdate(self, payLoad: bytes):
		if len(payLoad) == 0:
			return 0
		assert len(payLoad) == 1
		return ord(payLoad)

	def _get_numCells(self) -> int:
		return self._attributeHandlers[protocol.BrailleAttribute.NUM_CELLS].value

	def display(self, cells: List[int]):
		# cells will already be padded up to numCells.
		arg = bytes(cells)
		self.writeMessage(protocol.BrailleCommand.DISPLAY, arg)

BrailleDisplayDriver = RemoteBrailleDisplayDriver
