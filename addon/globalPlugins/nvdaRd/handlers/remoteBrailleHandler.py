from ._remoteHandler import RemoteHandler
import braille
import brailleInput
from hwIo import intToByte
import typing
import inputCore
from ._remoteHandler import RemoteFocusState


if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleHandler(RemoteHandler):
	driverType = protocol.DriverType.BRAILLE

	_currentDisplay: braille.BrailleDisplayDriver

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		super().__init__(pipeName, isNamedPipeClient)
		inputCore.decide_executeGesture.register(self._handleExecuteGesture)
		braille.decide_enabled.register(self._handleBrailleHandlerEnabled)

	def terminate(self):
		braille.decide_enabled.unregister(self._handleBrailleHandlerEnabled)
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		return super().terminate()

	def _get__currentDisplay(self):
		return braille.handler.display

	@protocol.attributeSender(protocol.BrailleAttribute.NUM_CELLS)
	def _sendNumCells(self) -> bytes:
		return intToByte(self._currentDisplay.numCells)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _sendGestureMap(self) -> bytes:
		return self._pickle(self._currentDisplay.gestureMap)

	@protocol.commandHandler(protocol.BrailleCommand.DISPLAY)
	def _handleDisplay(self, payload: bytes):
		cells = list(payload)
		if braille.handler.displaySize > 0 and self.hasFocus == RemoteFocusState.SESSION_FOCUSED:
			# We use braille.handler._writeCells since this respects thread safe displays
			# and automatically falls back to noBraille if desired
			# Execute it on the main thread
			self._queueFunctionOnMainThread(braille.handler._writeCells, cells)

	def _handleExecuteGesture(self, gesture):
		if (
			isinstance(gesture, braille.BrailleDisplayGesture)
			and self.hasFocus == RemoteFocusState.SESSION_FOCUSED
		):
			kwargs = dict(
				source=gesture.source,
				id=gesture.id,
				routingIndex=gesture.routingIndex,
				model=self.model
			)
			if isinstance(gesture, brailleInput.BrailleInputGesture):
				kwargs['dots'] = gesture.dots
				kwargs['space'] = gesture.space
			newGesture = protocol.braille.BrailleInputGesture(**kwargs)
			self.writeMessage(protocol.BrailleCommand.EXECUTE_GESTURE, self._pickle(newGesture))
			return False
		return True

	def _handleBrailleHandlerEnabled(self):
		return self.hasFocus != RemoteFocusState.SESSION_FOCUSED
