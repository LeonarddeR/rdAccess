# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import typing

import addonHandler
import braille
import inputCore
from logHandler import log

if typing.TYPE_CHECKING:
	from ..lib import detection, driver, nvdaCompat, protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")
	driver = addon.loadModule("lib.driver")
	nvdaCompat = addon.loadModule("lib.nvdaCompat")
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleDisplayDriver(driver.RemoteDriver, nvdaCompat.BrailleDisplayDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote Braille")
	isThreadSafe = True
	supportsAutomaticDetection = True
	driverType = protocol.DriverType.BRAILLE
	_requiredAttributesOnInit = frozenset(
		driver.RemoteDriver._requiredAttributesOnInit.union({
			protocol.BrailleAttribute.NUM_CELLS,
		}),
	)

	@classmethod
	def registerAutomaticDetection(cls, driverRegistrar):
		driverRegistrar.addDeviceScanner(detection.bgScanRD, moveToStart=True)

	def _getModifierGestures(self, model: str | None = None):
		"""Hacky override that throws an instance at the underlying class method.
		If we don't do this, the method can't acces the gesture map at the instance level.
		"""
		# Deliberately calls the underlying classmethod function with an instance instead of
		# the class; ty can't model this reflection hack.
		modifierGesturesFunc = typing.cast(classmethod, super()._getModifierGestures).__func__
		return modifierGesturesFunc(self, model)  # ty: ignore[invalid-argument-type]

	def _handleRemoteDisconnect(self):
		# Raise an exception because handleDisplayUnavailable expects one
		try:
			raise RuntimeError("remote client disconnected")
		except RuntimeError:
			assert braille.handler is not None
			braille.handler.handleDisplayUnavailable()

	_incoming_numCells = protocol.AttributeReceiver(protocol.BrailleAttribute.NUM_CELLS, defaultValue=0)

	def _get_numCells(self) -> int:
		if (value := self.numRows * self.numCols) == 0:
			value = self._getRemoteAttributeValueWithFallback(protocol.BrailleAttribute.NUM_CELLS)
		return value

	_incoming_numRows = protocol.AttributeReceiver(protocol.BrailleAttribute.NUM_ROWS, defaultValue=1)

	def _get_numRows(self) -> int:
		return self._getRemoteAttributeValueWithFallback(protocol.BrailleAttribute.NUM_ROWS)

	_incoming_numCols = protocol.AttributeReceiver(protocol.BrailleAttribute.NUM_COLS, defaultValue=0)

	def _get_numCols(self) -> int:
		return self._getRemoteAttributeValueWithFallback(protocol.BrailleAttribute.NUM_COLS)

	_incoming_gestureMapUpdate = protocol.AttributeReceiver(protocol.BrailleAttribute.GESTURE_MAP)

	@_incoming_gestureMapUpdate.defaultValueGetter
	def _default_gestureMap(self, _attribute: protocol.AttributeT):
		return inputCore.GlobalGestureMap()

	def _get_gestureMap(self) -> inputCore.GlobalGestureMap:
		return self._getRemoteAttributeValueWithFallback(protocol.BrailleAttribute.GESTURE_MAP)

	@protocol.commandHandler(protocol.RdMessageType.BRAILLE_INPUT)
	def _command_brailleInput(self, **kwargs):
		gesture = protocol.braille.BrailleInputGesture(**kwargs)
		assert inputCore.manager is not None
		try:
			inputCore.manager.executeGesture(gesture)
		except inputCore.NoInputGestureAction:
			log.error("Unexpected NoInputGestureAction", exc_info=True)

	def display(self, cells: list[int]):
		# cells will already be padded up to numCells.
		assert len(cells) == self.numCells
		if len(cells) == 0:
			return
		self.sendMessage(protocol.RdMessageType.DISPLAY, cells=cells)


BrailleDisplayDriver = RemoteBrailleDisplayDriver
