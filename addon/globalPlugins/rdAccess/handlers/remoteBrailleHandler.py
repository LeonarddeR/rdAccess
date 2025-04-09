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


_supportsDisplayDimensions = versionInfo.version_year >= 2025


class RemoteBrailleHandler(RemoteHandler[braille.BrailleDisplayDriver]):
	driverType = protocol.DriverType.BRAILLE
	_queuedWrite: list[int] | None = None
	_queuedWriteLock: threading.Lock

	def __init__(self, ioThread: IoThread, pipeName: str, isNamedPipeClient: bool = True):
		self._queuedWriteLock = threading.Lock()
		super().__init__(ioThread, pipeName, isNamedPipeClient=isNamedPipeClient)
		braille.decide_enabled.register(self._handleBrailleHandlerEnabled)
		braille.displayChanged.register(self._handleDriverChanged)
		postBrailleViewerToolToggledAction.register(self._handleDisplayDimensionChanges)
		inputCore.decide_executeGesture.register(self._handleExecuteGesture)

	def terminate(self):
		inputCore.decide_executeGesture.unregister(self._handleExecuteGesture)
		postBrailleViewerToolToggledAction.unregister(self._handleDisplayDimensionChanges)
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

	if _supportsDisplayDimensions:

		@protocol.attributeSender(protocol.BrailleAttribute.NUM_COLS)
		def _outgoing_numCols(self, numCols=None) -> bytes:
			if numCols is None:
				# Use the display dimensions of the local braille handler
				numCols = braille.handler.displayDimensions.numCols
			return intToByte(numCols)

		@protocol.attributeSender(protocol.BrailleAttribute.NUM_ROWS)
		def _outgoing_numRows(self, numRows=None) -> bytes:
			if numRows is None:
				# Use the display dimensions of the local braille handler
				numRows = braille.handler.displayDimensions.numRows
			return intToByte(numRows)

	@protocol.attributeSender(protocol.BrailleAttribute.GESTURE_MAP)
	def _outgoing_gestureMap(self, gestureMap: inputCore.GlobalGestureMap | None = None) -> bytes:
		if gestureMap is None:
			gestureMap = self._driver.gestureMap
		if gestureMap:
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
			except OSError:
				log.warning("Error calling _handleExecuteGesture", exc_info=True)
		return True

	def _handleBrailleHandlerEnabled(self):
		return not self.hasFocus

	def _handleDriverChanged(self, display: braille.BrailleDisplayDriver):
		self._handleDisplayDimensionChanges()
		super()._handleDriverChanged(display)
		self._attributeSenderStore(protocol.BrailleAttribute.GESTURE_MAP, gestureMap=display.gestureMap)

	def _handleDisplayDimensionChanges(self):
		self._attributeSenderStore(protocol.BrailleAttribute.NUM_CELLS)
		if _supportsDisplayDimensions:
			self._attributeSenderStore(protocol.BrailleAttribute.NUM_COLS)
			self._attributeSenderStore(protocol.BrailleAttribute.NUM_ROWS)

	def _handleNotifications(self, connected: bool):
		if not braille.handler.enabled:
			# There's no point in notifying of braille connections if the braille handler is disabled
			return
		super()._handleNotifications(connected)
