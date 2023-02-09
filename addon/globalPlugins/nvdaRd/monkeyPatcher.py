import synthDriverHandler
import bdDetect
import versionInfo
import typing
import braille

if typing.TYPE_CHECKING:
	from ...lib import detection
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")


class MonkeyPatcher:

	def _bgScan(
			self,
			detector: bdDetect.Detector,
			detectUsb: bool,
			detectBluetooth: bool,
			limitToDevices: typing.Optional[typing.List[str]]
	):
		detector._stopEvent.clear()
		for driver, match in detection.bgScanRD(limitToDevices=limitToDevices):
			if detector._stopEvent.isSet():
				return
			if limitToDevices and driver not in limitToDevices:
				continue
			if braille.handler.setDisplayByName(driver, detected=match):
				return
	self._originalBgScan(detector, )

	def patchBdDetect(self):


	def unpatchBdDetect(self):
		...

	def patchSynthDriverHandler(self):
		...

	def unpatchSynthDriverHandler(self):
		...

	def __init__(self):
		self.patchBdDetect()
		self.patchSynthDriverHandler()

	def terminate(self):
		self.unpatchSynthDriverHandler()
		self.unpatchBdDetect()
