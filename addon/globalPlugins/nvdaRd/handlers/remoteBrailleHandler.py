from ._remoteHandler import RemoteHandler
import braille
import brailleInput
from hwIo import intToByte
import typing
import inputCore
from ._remoteHandler import RemoteFocusState
import time
import sys
import api
from logHandler import log


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
		super().__init__(pipeName, isNamedPipeClient)
		self._focusLastSet = time.time()
		inputCore.decide_executeGesture.register(self._handleExecuteGesture)
		braille.decide_enabled.register(self._handleBrailleHandlerEnabled)

	def terminate(self):
		braille.decide_enabled.unregister(self._handleBrailleHandlerEnabled)
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		return super().terminate()

	def _get__driver(self):
		return braille.handler.display

	@protocol.attributeSender(protocol.BrailleAttribute.NUM_CELLS)
	def _outgoing_numCells(self) -> bytes:
		return intToByte(self._driver.numCells)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _outgoing_gestureMap(self) -> bytes:
		return self._pickle(self._driver.gestureMap)

	@protocol.commandHandler(protocol.BrailleCommand.DISPLAY)
	def _command_display(self, payload: bytes):
		cells = list(payload)
		if (
			braille.handler.displaySize > 0
			and not braille.handler.enabled
			and self.hasFocus == RemoteFocusState.SESSION_FOCUSED
		):
			# We use braille.handler._writeCells since this respects thread safe displays
			# and automatically falls back to noBraille if desired
			# Execute it on the main thread
			self._queueFunctionOnMainThread(braille.handler._writeCells, cells)

	def event_gainFocus(self, obj):
		self._focusLastSet = time.time()

	hasFocus: RemoteFocusState

	def _get_hasFocus(self) -> RemoteFocusState:
		remoteProcessHasFocus = api.getFocusObject().processID == self._dev.pipeProcessId
		if not remoteProcessHasFocus:
			return RemoteFocusState.NONE
		attribute = protocol.GenericAttribute.HAS_FOCUS
		log.debug("Requesting focus information from remote driver")
		if self._attributeValueProcessor.hasNewValueSince(attribute, self._focusLastSet):
			newValue = self._attributeValueProcessor.getValue(attribute)
			log.debug(f"Focus value changed since focus last set, set to {newValue}")
			return RemoteFocusState.SESSION_FOCUSED if newValue else RemoteFocusState.CLIENT_FOCUSED
		# Tell the remote system to intercept a incoming gesture.
		log.debug("Instructing remote system to intercept gesture")
		self.writeMessage(
			protocol.GenericCommand.INTERCEPT_GESTURE,
			self._pickle(self._focusTestGesture.normalizedIdentifiers)
		)
		self.REQUESTRemoteAttribute(protocol.GenericAttribute.HAS_FOCUS)
		log.debug("Sending focus test gesture")
		self._focusTestGesture.send()
		return RemoteFocusState.SESSION_PENDING

	@protocol.attributeReceiver(protocol.GenericAttribute.HAS_FOCUS, defaultValue=False)
	def _incoming_hasFocus(self, payload: bytes) -> bool:
		assert len(payload) == 1
		return bool.from_bytes(payload, byteorder=sys.byteorder)

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
