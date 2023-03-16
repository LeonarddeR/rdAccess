import bdDetect
import typing
import braille
from extensionPoints import Action
import synthDriverHandler
import gui.settingsDialogs

if typing.TYPE_CHECKING:
	from ...lib import detection
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")


class MonkeyPatcher:

	@staticmethod
	def _bgScan(
			self,
			detectUsb: bool,
			detectBluetooth: bool,
			limitToDevices: typing.Optional[typing.List[str]]
	):
		self._stopEvent.clear()
		for driver, match in detection.bgScanRD(limitToDevices=limitToDevices):
			if self._stopEvent.isSet():
				return
			if limitToDevices and driver not in limitToDevices:
				continue
			if braille.handler.setDisplayByName(driver, detected=match):
				return
		bdDetect.Detector._bgScan._origin(self, detectUsb, detectBluetooth, limitToDevices)

	@staticmethod
	def _setSynth(name: typing.Optional[str], isFallback: bool = False):
		res = synthDriverHandler.setSynth._origin(name, isFallback)
		if res:
			newSynth = synthDriverHandler.getSynth()
			synthDriverHandler.synthChanged.notify(
				synth=newSynth,
				audioOutputDevice=synthDriverHandler._audioOutputDevice,
				isFallback=isFallback
			)
		return res

	def patchBdDetect(self):
		if bdDetect.Detector._bgScan == self._bgScan:
			return
		self._bgScan._origin = bdDetect.Detector._bgScan
		bdDetect.Detector._bgScan = self._bgScan

	def patchSynthDriverHandler(self):
		if synthDriverHandler.setSynth == self._setSynth:
			return
		self._setSynth._origin = synthDriverHandler.setSynth
		synthDriverHandler.synthChanged = Action()
		gui.settingsDialogs.setSynth = synthDriverHandler.setSynth = self._setSynth

	def unpatchBdDetect(self):
		if bdDetect.Detector._bgScan != self._bgScan:
			return
		bdDetect.Detector._bgScan = self._bgScan._origin
		del self._bgScan._origin

	def unpatchSynthDriverHandler(self):
		if synthDriverHandler.setSynth != self._setSynth:
			return
		gui.settingsDialogs.setSynth = synthDriverHandler.setSynth = self._setSynth._origin
		del synthDriverHandler.synthChanged
		del self._setSynth._origin
