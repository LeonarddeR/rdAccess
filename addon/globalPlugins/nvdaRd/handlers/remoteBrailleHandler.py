from ._remoteHandler import RemoteHandler
import braille
import brailleInput
from hwIo import intToByte
import typing
import inputCore
import threading

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleHandler(RemoteHandler):
	driverType = protocol.DriverType.BRAILLE
	_driver: braille.BrailleDisplayDriver
	_queuedWrite: typing.Optional[typing.List[int]] = None
	_queuedWriteLock: threading.Lock

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		self._queuedWriteLock = threading.Lock()
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
			with self._queuedWriteLock:
				self._queuedWrite = cells
			if not braille.handler.enabled and self.hasFocus:
				self._queueFunctionOnMainThread(self._performLocalWriteCells)
			elif self._remoteSessionhasFocus is False:
				self.requestRemoteAttribute(protocol.GenericAttribute.TIME_SINCE_INPUT)

	def _performLocalWriteCells(self):
		with self._queuedWriteLock:
			data = self._queuedWrite
			self._queuedWrite = None
		if data:
			braille.handler._writeCells(data)

	def _handleRemoteSessionGainFocus(self):
		super()._handleRemoteSessionGainFocus()
		self._queueFunctionOnMainThread(self._performLocalWriteCells)

	def _handleExecuteGesture(self, gesture):
		if (
			isinstance(gesture, braille.BrailleDisplayGesture)
			and not braille.handler.enabled
			and self.hasFocus
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
		return not self.hasFocus

	def _handledisplayChanged(self, display: braille.BrailleDisplayDriver):
		self._attributeSenderStore(protocol.BrailleAttribute.NUM_CELLS, numCells=display.numCells	)
		self._attributeSenderStore(protocol.BrailleAttribute.GESTURE_MAP, gestureMap=display.gestureMap)
		self._attributeSenderStore(protocol.GenericAttribute.SUPPORTED_SETTINGS, settings=display.supportedSettings)
