import threading
from concurrent.futures import ThreadPoolExecutor, Future
import typing
import addonHandler
import synthDriverHandler
from baseObject import AutoPropertyObject
from synthDrivers.remote import remoteSynthDriver
import queueHandler

if typing.TYPE_CHECKING:
	from ...lib import detection
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")


class _SynthDetector(AutoPropertyObject):
	_prevSynth: typing.Optional[str] = None

	def __init__(self):
		remoteSynthDriver.synthRemoteDisconnected.register(self._handleRemoteDisconnect)
		self._executor = ThreadPoolExecutor(1)
		self._queuedFuture: typing.Optional[Future] = None
		self._stopEvent = threading.Event()

	currentSynthesizer: synthDriverHandler.SynthDriver

	def _get_currentSynthesizer(self) -> synthDriverHandler.SynthDriver:
		return synthDriverHandler.getSynth()

	def _set_currentSynthesizer(self, synth):
		curSynth = self._get_currentSynthesizer()
		curSynth.cancel()
		curSynth.terminate()
		self._prevSynth = curSynth.name
		synthDriverHandler._curSynth = synth

	isRemoteSynthActive: bool

	def _get_isRemoteSynthActive(self):
		return isinstance(self.currentSynthesizer, remoteSynthDriver)

	def _handleRemoteDisconnect(self, synth: remoteSynthDriver):
		queueHandler.queueFunction(queueHandler.eventQueue, self._fallbackToPrevSynth)

	def _fallbackToPrevSynth(self):
		if self._prevSynth is not None:
			synthDriverHandler.setSynth(self._prevSynth)
			self._prevSynth = None
		else:
			synthDriverHandler.findAndSetNextSynth(remoteSynthDriver.name)

	def _queueBgScan(self):
		if self.isRemoteSynthActive:
			return
		if self._queuedFuture:
			self._queuedFuture.cancel()
		self._queuedFuture = self._executor.submit(self._bgScan)

	def _stopBgScan(self):
		"""Stops the current scan as soon as possible and prevents a queued scan to start."""
		self._stopEvent.set()
		if self._queuedFuture:
			# This will cancel a queued scan (i.e. not the currently running scan, if any)
			# If this future belongs to a scan that is currently running or finished, this does nothing.
			self._queuedFuture.cancel()

	def _bgScan(self):
		self._stopEvent.clear()
		if self.isRemoteSynthActive:
			return
		iterator = detection.bgScanRD(driverType=detection.DriverType.SPEECH)
		for driver, match in iterator:
			if self._stopEvent.is_set():
				return
			driverClass = synthDriverHandler._getSynthDriver(driver)
			assert issubclass(driverClass, remoteSynthDriver)
			try:
				driverInst: remoteSynthDriver = driverClass(match)
				driverInst.initSettings()
			except RuntimeError:
				if self._stopEvent.is_set():
					return
				continue
			self.currentSynthesizer = driverInst
			self._stopBgScan()
			return

	def rescan(self):
		self._stopBgScan()
		self._queueBgScan()

	def terminate(self):
		remoteSynthDriver.synthRemoteDisconnected.unregister(self._handleRemoteDisconnect)
		self._stopBgScan()
		self._executor.shutdown(wait=False)
