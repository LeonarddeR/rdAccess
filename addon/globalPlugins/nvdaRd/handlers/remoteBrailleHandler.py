from ._remoteHandler import RemoteHandler
import braille
import brailleInput
from hwIo import intToByte
import typing
import inputCore
import time
from ._remoteHandler import RemoteFocusState

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleHandler(RemoteHandler):
	driverType = protocol.DriverType.BRAILLE
	_driver: braille.BrailleDisplayDriver

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		self._focusLastSet = time.time()
		braille.decide_enabled.register(self._handleBrailleHandlerEnabled)
		braille.displayChanged.register(self._handledisplayChanged)
		inputCore.decide_executeGesture.register(self._handleExecuteGesture)
		super().__init__(pipeName, isNamedPipeClient)

	def terminate(self):
		super().terminate()
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		braille.displayChanged.unregister(self._handledisplayChanged)
		braille.decide_enabled.unregister(self._handleBrailleHandlerEnabled)

	def _get__driver(self):
		return braille.handler.display

	@protocol.attributeSender(protocol.BrailleAttribute.NUM_CELLS)
	def _outgoing_numCells(self, numCells=None) -> bytes:
		if numCells is None:
			numCells = self._driver.numCells
		return intToByte(numCells)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _outgoing_gestureMap(self, gestureMap: typing.Optional[inputCore.GlobalGestureMap] = None) -> bytes:
		if gestureMap is None:
			gestureMap = self._driver.gestureMap
		return self._pickle(gestureMap)

	@protocol.commandHandler(protocol.BrailleCommand.DISPLAY)
	def _command_display(self, payload: bytes):
		cells = list(payload)
		if braille.handler.displaySize > 0:
			if not braille.handler.enabled and self.hasFocus == RemoteFocusState.SESSION_FOCUSED:
				# We use braille.handler._writeCells since this respects thread safe displays
				# and automatically falls back to noBraille if desired
				# Execute it on the main thread
				self._queueFunctionOnMainThread(braille.handler._writeCells, cells)
			elif self.hasFocus == RemoteFocusState.CLIENT_FOCUSED:
				self.requestRemoteAttribute(protocol.GenericAttribute.TIME_SINCE_INPUT)

	def _handleExecuteGesture(self, gesture):
		if (
			isinstance(gesture, braille.BrailleDisplayGesture)
			and not braille.handler.enabled
			and self.hasFocus == RemoteFocusState.SESSION_FOCUSED
		):
			kwargs = dict(
				source=gesture.source,
				id=gesture.id,
				routingIndex=gesture.routingIndex,
				model=gesture.model
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

	def _handledisplayChanged(self, display: braille.BrailleDisplayDriver):
		self._attributeSenderStore(protocol.BrailleAttribute.NUM_CELLS, numCells=display.numCells	)
		self._attributeSenderStore(protocol.BrailleAttribute.GESTURE_MAP, gestureMap=display.gestureMap)
		self._attributeSenderStore(protocol.GenericAttribute.SUPPORTED_SETTINGS, settings=display.supportedSettings)
