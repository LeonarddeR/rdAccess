# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import braille
import typing
import addonHandler
from typing import List
import inputCore
from logHandler import log

if typing.TYPE_CHECKING:
	from ..lib import detection
	from ..lib import driver
	from ..lib import protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class RemoteBrailleDisplayDriver(driver.RemoteDriver, braille.BrailleDisplayDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote Braille")
	isThreadSafe = True
	supportsAutomaticDetection = True
	driverType = protocol.DriverType.BRAILLE

	@classmethod
	def registerAutomaticDetection(cls, driverRegistrar):
		driverRegistrar.addDeviceScanner(detection.bgScanRD, moveToStart=True)

	def _getModifierGestures(self, model: typing.Optional[str] = None):
		"""Hacky override that throws an instance at the underlying class method.
		If we don't do this, the method can't acces the gesture map at the instance level.
		"""
		return super()._getModifierGestures.__func__(self, model)

	def _handleRemoteDisconnect(self):
		# Raise an exception because handleDisplayUnavailable expects one
		try:
			raise RuntimeError("remote client disconnected")
		except RuntimeError:
			braille.handler.handleDisplayUnavailable()

	@protocol.attributeReceiver(protocol.BrailleAttribute.NUM_CELLS, defaultValue=0)
	def _incoming_numCells(self, payload: bytes) -> int:
		assert len(payload) == 1
		return ord(payload)

	def _get_numCells(self) -> int:
		attribute = protocol.BrailleAttribute.NUM_CELLS
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value

	@protocol.attributeReceiver(protocol.BrailleAttribute.GESTURE_MAP)
	def _incoming_gestureMapUpdate(self, payload: bytes) -> inputCore.GlobalGestureMap:
		assert len(payload) > 0
		return self._unpickle(payload)

	@_incoming_gestureMapUpdate.defaultValueGetter
	def _default_gestureMap(self, attribute: protocol.AttributeT):
		return inputCore.GlobalGestureMap()

	def _get_gestureMap(self) -> inputCore.GlobalGestureMap:
		attribute = protocol.BrailleAttribute.GESTURE_MAP
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value

	@protocol.commandHandler(protocol.BrailleCommand.EXECUTE_GESTURE)
	def _command_executeGesture(self, payload: bytes):
		assert len(payload) > 0
		gesture = self._unpickle(payload)
		try:
			inputCore.manager.executeGesture(gesture)
		except inputCore.NoInputGestureAction:
			log.error("Unexpected NoInputGestureAction", exc_info=True)

	def display(self, cells: List[int]):
		# cells will already be padded up to numCells.
		assert len(cells) == self.numCells
		if len(cells) == 0:
			return
		arg = bytes(cells)
		self.writeMessage(protocol.BrailleCommand.DISPLAY, arg)


BrailleDisplayDriver = RemoteBrailleDisplayDriver
