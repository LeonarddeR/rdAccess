# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import threading
from concurrent.futures import ThreadPoolExecutor, Future
import typing
import addonHandler
import synthDriverHandler
from baseObject import AutoPropertyObject
from synthDrivers.remote import remoteSynthDriver
import queueHandler
import config
from logHandler import log
from braille import AUTOMATIC_PORT

if typing.TYPE_CHECKING:
    from ...lib import detection
else:
    addon: addonHandler.Addon = addonHandler.getCodeAddon()
    detection = addon.loadModule("lib.detection")


class _SynthDetector(AutoPropertyObject):
    def __init__(self):
        remoteSynthDriver.synthRemoteDisconnected.register(self._handleRemoteDisconnect)
        self._executor = ThreadPoolExecutor(1, thread_name_prefix=self.__class__.__name__)
        self._queuedFuture: typing.Optional[Future] = None
        self._stopEvent = threading.Event()

    currentSynthesizer: synthDriverHandler.SynthDriver

    def _get_currentSynthesizer(self) -> synthDriverHandler.SynthDriver:
        return synthDriverHandler.getSynth()

    def _set_currentSynthesizer(self, synth):
        curSynth = self._get_currentSynthesizer()
        curSynth.cancel()
        curSynth.terminate()
        synthDriverHandler._curSynth = synth

    isRemoteSynthActive: bool

    def _get_isRemoteSynthActive(self):
        return isinstance(self.currentSynthesizer, remoteSynthDriver)

    isRemoteSynthConfigured: bool

    def _get_isRemoteSynthConfigured(self):
        return config.conf[remoteSynthDriver._configSection]["synth"] == remoteSynthDriver.name

    def _handleRemoteDisconnect(self, synth: remoteSynthDriver):
        log.error(f"Handling remote disconnect for {synth!r}")
        queueHandler.queueFunction(queueHandler.eventQueue, self._fallback)

    def _fallback(self):
        fallback = (
            config.conf[remoteSynthDriver._configSection]
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
        remoteSynthDriver.synthRemoteDisconnected.unregister(self._handleRemoteDisconnect)
        self._stopBgScan()
        self._executor.shutdown(wait=False)
