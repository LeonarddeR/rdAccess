# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

from __future__ import annotations

import os.path
import typing
from collections import OrderedDict

import addonHandler
import globalVars
import nvwave
import synthDriverHandler
import tones
from autoSettingsUtils.driverSetting import DriverSetting
from autoSettingsUtils.utils import StringParameterInfo
from extensionPoints import Action
from languageHandler import getLanguage
from logHandler import log
from speech.commands import IndexCommand

if typing.TYPE_CHECKING:
	from ..lib import driver, protocol
	from ..lib.nvdaCompat import BRAILLE_AUTOMATIC_PORT as AUTOMATIC_PORT
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")
	nvdaCompat = addon.loadModule("lib.nvdaCompat")
	AUTOMATIC_PORT = nvdaCompat.BRAILLE_AUTOMATIC_PORT


class remoteSynthDriver(driver.RemoteDriver, synthDriverHandler.SynthDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote speech")
	supportedNotifications = {
		synthDriverHandler.synthIndexReached,
		synthDriverHandler.synthDoneSpeaking,
	}
	driverType = protocol.DriverType.SPEECH
	synthRemoteDisconnected = Action()
	fallbackSynth: str = AUTOMATIC_PORT[0]
	_localSettings: typing.ClassVar = [
		DriverSetting(
			id="fallbackSynth",
			# Translators: The name of a remote synthesizer setting to select the fallback synthesizer.
			displayNameWithAccelerator=_("&Fallback synthesizer"),
			availableInSettingsRing=True,
			defaultVal=fallbackSynth,
		),
	]

	@classmethod
	def _get_availableFallbacksynths(cls):
		dct = OrderedDict()
		dct[AUTOMATIC_PORT[0]] = StringParameterInfo(*AUTOMATIC_PORT)
		dct.update(
			(n, StringParameterInfo(n, d)) for n, d in synthDriverHandler.getSynthList() if n != cls.name
		)
		return dct

	def __init__(self, port="auto"):
		super().__init__(port)
		nvwave.decide_playWaveFile.register(self.handle_decidePlayWaveFile)
		tones.decide_beep.register(self.handle_decideBeep)

	def initSettings(self):
		super().initSettings()
		synthDriverHandler.changeVoice(self, None)

	def terminate(self):
		tones.decide_beep.unregister(self.handle_decideBeep)
		nvwave.decide_playWaveFile.unregister(self.handle_decidePlayWaveFile)
		super().terminate()

	def handle_decideBeep(self, **kwargs) -> bool:
		log.debug(f"Sending TONE command: {kwargs}")
		try:
			self.sendMessage(protocol.RdMessageType.TONE, **kwargs)
		except OSError:
			log.warning("Error calling handle_decideBeep", exc_info=True)
			return True
		return False

	def handle_decidePlayWaveFile(self, **kwargs) -> bool:
		kwargs["fileName"] = os.path.relpath(kwargs["fileName"], globalVars.appDir)
		log.debug(f"Sending WAVE command: {kwargs}")
		try:
			self.sendMessage(protocol.RdMessageType.WAVE, **kwargs)
		except OSError:
			log.warning("Error calling handle_decidePlayWaveFile", exc_info=True)
			return True
		return False

	def _handleRemoteDisconnect(self):
		self.synthRemoteDisconnected.notify(synth=self)

	def speak(self, speechSequence):
		try:
			self.sendMessage(protocol.RdMessageType.SPEAK, sequence=speechSequence)
		except OSError:
			log.error("Error speaking", exc_info=True)
			self._handleRemoteDisconnect()

	def cancel(self):
		try:
			self.sendMessage(protocol.RdMessageType.CANCEL)
		except OSError:
			log.warning("Error cancelling speech", exc_info=True)

	def pause(self, switch):
		try:
			self.sendMessage(protocol.RdMessageType.PAUSE_SPEECH, switch=switch)
		except OSError:
			log.warning("Error pausing speech", exc_info=True)

	def _getAvailableVoices(self) -> OrderedDict:
		"""Return an empty OrderedDict as a fallback.

		The actual available voices are retrieved through the settings accessor
		from the remote synth driver. This override prevents NotImplementedError
		from being raised when availableVoices is accessed before the remote
		attribute has been received.
		"""
		return OrderedDict()

	_incoming_supportedCommands = protocol.AttributeReceiver(
		protocol.SpeechAttribute.SUPPORTED_COMMANDS,
		defaultValue=frozenset({IndexCommand}),
	)

	def _get_supportedCommands(self):
		return self._getRemoteAttributeValueWithFallback(protocol.SpeechAttribute.SUPPORTED_COMMANDS)

	_incoming_language = protocol.AttributeReceiver(
		protocol.SpeechAttribute.LANGUAGE,
		defaultValue=getLanguage(),
	)

	def _get_language(self):
		return self._getRemoteAttributeValueWithFallback(protocol.SpeechAttribute.LANGUAGE)

	@protocol.commandHandler(protocol.RdMessageType.INDEX)
	def _command_indexReached(self, index: int):
		if index:
			synthDriverHandler.synthIndexReached.notify(synth=self, index=index)
		else:
			synthDriverHandler.synthDoneSpeaking.notify(synth=self)

	def _handleRemoteDriverChange(self):
		super()._handleRemoteDriverChange()
		synthDriverHandler.changeVoice(self, None)


SynthDriver = remoteSynthDriver
