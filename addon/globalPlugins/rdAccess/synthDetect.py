# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import threading
import typing
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

import addonHandler
import config
import queueHandler
import synthDriverHandler
from baseObject import AutoPropertyObject
from logHandler import log
from synthDrivers.remote import remoteSynthDriver

if typing.TYPE_CHECKING:
	from ...lib import detection
	from ...lib.nvdaCompat import BRAILLE_AUTOMATIC_PORT as AUTOMATIC_PORT
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	detection = addon.loadModule("lib.detection")
	nvdaCompat = addon.loadModule("lib.nvdaCompat")
	AUTOMATIC_PORT = nvdaCompat.BRAILLE_AUTOMATIC_PORT


class SynthDetector(AutoPropertyObject):
	#: NVDA's own synthesizer profile switch handler, while replaced by ours.
	_nvdaHandlePostConfigProfileSwitch: Callable[[bool], None] | None = None

	def __init__(self):
		remoteSynthDriver.synthRemoteDisconnected.register(self._handleRemoteDisconnect)
		self._executor = ThreadPoolExecutor(1, thread_name_prefix=self.__class__.__name__)
		self._queuedFuture: Future | None = None
		self._stopEvent = threading.Event()
		self._takeOverPostConfigProfileSwitch()

	currentSynthesizer: synthDriverHandler.SynthDriver

	def _get_currentSynthesizer(self) -> synthDriverHandler.SynthDriver | None:
		return synthDriverHandler.getSynth()

	def _set_currentSynthesizer(self, synth):
		curSynth = self._get_currentSynthesizer()
		assert curSynth is not None
		curSynth.cancel()
		curSynth.terminate()
		synthDriverHandler._curSynth = synth

	isRemoteSynthActive: bool

	def _get_isRemoteSynthActive(self):
		return isinstance(self.currentSynthesizer, remoteSynthDriver)

	isRemoteSynthConfigured: bool

	def _get_isRemoteSynthConfigured(self):
		assert config.conf is not None
		return config.conf[remoteSynthDriver._configSection]["synth"] == remoteSynthDriver.name

	def _takeOverPostConfigProfileSwitch(self):
		"""Puts our own handler in NVDA's place, both on L{config.post_configProfileSwitch}
		and as L{synthDriverHandler.handlePostConfigProfileSwitch},
		at the start of the registration order.
		"""
		if self._nvdaHandlePostConfigProfileSwitch is not None:
			return
		original = synthDriverHandler.handlePostConfigProfileSwitch
		if not config.post_configProfileSwitch.unregister(original):
			log.debugWarning("NVDA's synthesizer profile switch handler was not registered")
		self._nvdaHandlePostConfigProfileSwitch = original
		handler = self._handlePostConfigProfileSwitch
		config.post_configProfileSwitch.register(handler)
		config.post_configProfileSwitch.moveToEnd(handler, last=False)
		synthDriverHandler.handlePostConfigProfileSwitch = handler  # ty: ignore[invalid-assignment]

	def _restorePostConfigProfileSwitch(self):
		"""Reverses L{_takeOverPostConfigProfileSwitch}.
		The module attribute is only restored when it still holds our handler.
		"""
		original = self._nvdaHandlePostConfigProfileSwitch
		if original is None:
			return
		self._nvdaHandlePostConfigProfileSwitch = None
		handler = self._handlePostConfigProfileSwitch
		config.post_configProfileSwitch.unregister(handler)
		config.post_configProfileSwitch.register(original)
		config.post_configProfileSwitch.moveToEnd(original, last=False)
		if synthDriverHandler.handlePostConfigProfileSwitch != handler:
			return
		synthDriverHandler.handlePostConfigProfileSwitch = original  # ty: ignore[invalid-assignment]

	def _handlePostConfigProfileSwitch(self, resetSpeechIfNeeded: bool = True):
		"""Skips NVDA's synthesizer reload while remote speech is active without being configured."""
		if self.isRemoteSynthActive and not self.isRemoteSynthConfigured:
			return
		assert self._nvdaHandlePostConfigProfileSwitch is not None
		self._nvdaHandlePostConfigProfileSwitch(resetSpeechIfNeeded)

	def _handleRemoteDisconnect(self, synth: remoteSynthDriver):
		log.error(f"Handling remote disconnect for {synth!r}")
		queueHandler.queueFunction(queueHandler.eventQueue, self._fallback)

	def _fallback(self):
		assert config.conf is not None
		fallback = (
			config
			.conf[remoteSynthDriver._configSection]
			.get(remoteSynthDriver.name, {})
			.get("fallbackSynth", AUTOMATIC_PORT[0])
		)
		if fallback != AUTOMATIC_PORT[0]:
			synthDriverHandler.setSynth(fallback, isFallback=True)
		else:
			synthDriverHandler.findAndSetNextSynth(remoteSynthDriver.name)

	def _queueBgScan(self, force: bool = False):
		if self.isRemoteSynthActive or not (force or self.isRemoteSynthConfigured):
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

	def rescan(self, force: bool = False):
		self._stopBgScan()
		self._queueBgScan(force)

	def terminate(self):
		self._restorePostConfigProfileSwitch()
		remoteSynthDriver.synthRemoteDisconnected.unregister(self._handleRemoteDisconnect)
		self._stopBgScan()
		self._executor.shutdown(wait=False)
