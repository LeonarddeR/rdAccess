# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import threading
import typing

import braille
import brailleInput
import inputCore
import versionInfo
from brailleViewer import postBrailleViewerToolToggledAction
from hwIo import IoThread, intToByte
from logHandler import log

from ._remoteHandler import RemoteHandler

if typing.TYPE_CHECKING:
	from ....lib import protocol
else:
	import addonHandler

	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleHandler(RemoteHandler):
	driverType = protocol.DriverType.BRAILLE
	_driver: braille.BrailleDisplayDriver
	_queuedWrite: typing.Optional[typing.List[int]] = None
	_queuedWriteLock: threading.Lock

	def __init__(self, ioThread: IoThread, pipeName: str, isNamedPipeClient: bool = True):
		self._queuedWriteLock = threading.Lock()
		super().__init__(ioThread, pipeName, isNamedPipeClient=isNamedPipeClient)
		braille.decide_enabled.register(self._handleBrailleHandlerEnabled)
		braille.displayChanged.register(self._handleDriverChanged)
		postBrailleViewerToolToggledAction.register(self._handlePostBrailleViewerToolToggled)
		inputCore.decide_executeGesture.register(self._handleExecuteGesture)

	def terminate(self):
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		postBrailleViewerToolToggledAction.unregister(self._handlePostBrailleViewerToolToggled)
		braille.displayChanged.unregister(self._handleDriverChanged)
		braille.decide_enabled.unregister(self._handleBrailleHandlerEnabled)
		super().terminate()

	def _get__driver(self):
		return braille.handler.display

	@protocol.attributeSender(protocol.BrailleAttribute.NUM_CELLS)
	def _outgoing_numCells(self, numCells=None) -> bytes:
		if numCells is None:
			# Use the display size of the local braille handler
			numCells = braille.handler.displaySize
		return intToByte(numCells)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _outgoing_gestureMap(self, gestureMap: typing.Optional[inputCore.GlobalGestureMap] = None) -> bytes:
		if gestureMap is None:
			gestureMap = self._driver.gestureMap
		if gestureMap and not (versionInfo.version_year == 2023 and versionInfo.version_major == 1):
			export = gestureMap.export()
			gestureMap = inputCore.GlobalGestureMap(export)
			gestureMap.update(inputCore.manager.userGestureMap.export())
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
				model=gesture.model,
			)
			if isinstance(gesture, brailleInput.BrailleInputGesture):
				kwargs["dots"] = gesture.dots
				kwargs["space"] = gesture.space
			newGesture = protocol.braille.BrailleInputGesture(**kwargs)
			try:
				self.writeMessage(protocol.BrailleCommand.EXECUTE_GESTURE, self._pickle(newGesture))
				return False
			except WindowsError:
				log.warning("Error calling _handleExecuteGesture", exc_info=True)
		return True

	def _handleBrailleHandlerEnabled(self):
		return not self.hasFocus

	def _handleDriverChanged(self, display: braille.BrailleDisplayDriver):
		self._attributeSenderStore(protocol.BrailleAttribute.NUM_CELLS)
		super()._handleDriverChanged(display)
		self._attributeSenderStore(protocol.BrailleAttribute.GESTURE_MAP, gestureMap=display.gestureMap)

	def _handlePostBrailleViewerToolToggled(self):
		self._attributeSenderStore(protocol.BrailleAttribute.NUM_CELLS)
