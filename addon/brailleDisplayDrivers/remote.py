import braille
import typing
import addonHandler
from typing import List
import inputCore
import sys
import keyboardHandler
from logHandler import log
import time

if typing.TYPE_CHECKING:
	from ..lib import driver
	from ..lib import protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleDisplayDriver(driver.RemoteDriver, braille.BrailleDisplayDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote Braille")
	isThreadSafe = True
	driverType = protocol.DriverType.BRAILLE

	def _handleRemoteDisconnect(self):
		# Raise an exception because handleDisplayUnavailable expects one
		try:
			raise RuntimeError("XOFF received, remote client disconnected")
		except RuntimeError:
			braille.handler.handleDisplayUnavailable()

	@protocol.commandHandler(protocol.GenericCommand.INTERCEPT_GESTURE)
	def _interceptGesture(self, payload: bytes):
		intercepting = self._unpickle(payload=payload)
		log.debug(f"Instructed to intercept gesture {intercepting!r}")
		self._gesturesToIntercept.append(intercepting)

	@protocol.attributeSender(protocol.GenericAttribute.HAS_FOCUS)
	def _sendHasFocus(self) -> bytes:
		initialTime = time.time()
		result = self._safeWait(lambda: self._lastKeyboardGestureInputTime >= initialTime, timeout=self.timeout)
		return result.to_bytes(1, sys.byteorder)

	def _handleDecideExecuteGesture(self, gesture):
		if isinstance(gesture, keyboardHandler.KeyboardInputGesture):
			self._lastKeyboardGestureInputTime = time.time()
			intercepting = next(
				(t for t in self._gesturesToIntercept if any(i for i in t if i in gesture.normalizedIdentifiers)),
				None
			)
			if intercepting is not None:
				self._gesturesToIntercept.remove(intercepting)
				log.debug(f"Intercepted gesture, execution canceled: {intercepting!r}")
				return False
		return True

	def __init__(self, port="auto"):
		super().__init__()
		self._lastKeyboardGestureInputTime = time.time()
		self._gesturesToIntercept: List[List[str]] = []
		inputCore.decide_executeGesture.register(self._handleDecideExecuteGesture)

	def terminate(self):
		inputCore.decide_executeGesture.unregister(self._handleDecideExecuteGesture)
		return super().terminate()

	@protocol.attributeReceiver(protocol.BrailleAttribute.NUM_CELLS, defaultValue=0)
	def _incoming_numCells(self, payload: bytes) -> int:
		assert len(payload) == 1
		return ord(payload)

	def _get_numCells(self) -> int:
		return self.getRemoteAttribute(protocol.BrailleAttribute.NUM_CELLS, allowCache=True, fallBackToDefault=True)

	@protocol.attributeReceiver(protocol.BrailleAttribute.GESTURE_MAP)
	def _incoming_gestureMapUpdate(self, payload: bytes) -> inputCore.GlobalGestureMap:
		assert len(payload) > 0
		return self._unpickle(payload)

	@_incoming_gestureMapUpdate.defaultValueGetter
	def _default_gestureMap(self, attribute: protocol.AttributeT):
		return inputCore.GlobalGestureMap()

	def _get_gestureMap(self) -> inputCore.GlobalGestureMap:
		return self.getRemoteAttribute(protocol.BrailleAttribute.GESTURE_MAP, allowCache=True, fallBackToDefault=True)

	@protocol.commandHandler(protocol.BrailleCommand.EXECUTE_GESTURE)
	def _command_executeGesture(self, payload: bytes):
		assert len(payload) > 0
		gesture = self._unpickle(payload)
		inputCore.manager.executeGesture(gesture)

	def display(self, cells: List[int]):
		# cells will already be padded up to numCells.
		arg = bytes(cells)
		self.writeMessage(protocol.BrailleCommand.DISPLAY, arg)


BrailleDisplayDriver = RemoteBrailleDisplayDriver
