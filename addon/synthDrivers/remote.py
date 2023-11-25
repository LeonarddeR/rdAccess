# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os.path
import sys
import typing
from collections import OrderedDict
from typing import Optional

import addonHandler
import globalVars
import nvwave
import synthDriverHandler
import tones
from autoSettingsUtils.driverSetting import DriverSetting
from autoSettingsUtils.utils import StringParameterInfo
from braille import AUTOMATIC_PORT
from extensionPoints import Action
from hwIo import boolToByte
from languageHandler import getLanguage
from logHandler import log

if typing.TYPE_CHECKING:
	from ..lib import driver, protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class remoteSynthDriver(driver.RemoteDriver, synthDriverHandler.SynthDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote speech")
	supportedNotifications = {
		synthDriverHandler.synthIndexReached,
		synthDriverHandler.synthDoneSpeaking,
	}
	driverType = protocol.DriverType.SPEECH
	synthRemoteDisconnected = Action()
	fallbackSynth: str
	_localSettings = [
		DriverSetting(
			id="fallbackSynth",
			# Translators: The name of a remote synthesizer setting to select the fallback synthesizer.
			displayNameWithAccelerator=_("&Fallback synthesizer"),
			availableInSettingsRing=True,
			defaultVal=AUTOMATIC_PORT[0],
		)
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

	def terminate(self):
		tones.decide_beep.unregister(self.handle_decideBeep)
		nvwave.decide_playWaveFile.unregister(self.handle_decidePlayWaveFile)
		super().terminate()

	def handle_decideBeep(self, **kwargs) -> bool:
		log.debug(f"Sending BEEP command: {kwargs}")
		try:
			self.writeMessage(protocol.SpeechCommand.BEEP, self._pickle(kwargs))
		except OSError:
			log.warning("Error calling handle_decideBeep", exc_info=True)
			return True
		return False

	def handle_decidePlayWaveFile(self, **kwargs) -> bool:
		kwargs["fileName"] = os.path.relpath(kwargs["fileName"], globalVars.appDir)
		log.debug(f"Sending PLAY_WAVE_FILE command: {kwargs}")
		try:
			self.writeMessage(protocol.SpeechCommand.PLAY_WAVE_FILE, self._pickle(kwargs))
		except OSError:
			log.warning("Error calling handle_decidePlayWaveFile", exc_info=True)
			return True
		return False

	def _handleRemoteDisconnect(self):
		self.synthRemoteDisconnected.notify(synth=self)

	def speak(self, speechSequence):
		try:
			self.writeMessage(protocol.SpeechCommand.SPEAK, self._pickle(speechSequence))
		except OSError:
			log.error("Error speaking", exc_info=True)
			self._handleRemoteDisconnect()

	def cancel(self):
		try:
			self.writeMessage(protocol.SpeechCommand.CANCEL)
		except OSError:
			log.warning("Error cancelling speech", exc_info=True)

	def pause(self, switch):
		try:
			self.writeMessage(protocol.SpeechCommand.PAUSE, boolToByte(switch))
		except OSError:
			log.warning("Error pausing speech", exc_info=True)

	@protocol.attributeReceiver(protocol.SpeechAttribute.SUPPORTED_COMMANDS, defaultValue=frozenset())
	def _incoming_supportedCommands(self, payLoad: bytes) -> frozenset:
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	def _get_supportedCommands(self):
		attribute = protocol.SpeechAttribute.SUPPORTED_COMMANDS
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue=getLanguage())
	def _incoming_language(self, payload: bytes) -> Optional[str]:
		assert len(payload) > 0
		return self._unpickle(payload)

	def _get_language(self):
		attribute = protocol.SpeechAttribute.LANGUAGE
		try:
			value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			value = self._attributeValueProcessor._getDefaultValue(attribute)
			self.requestRemoteAttribute(attribute)
		return value

	@protocol.commandHandler(protocol.SpeechCommand.INDEX_REACHED)
	def _command_indexReached(self, incomingPayload: bytes):
		assert len(incomingPayload) == 2
		index = int.from_bytes(incomingPayload, sys.byteorder)
		if index:
			synthDriverHandler.synthIndexReached.notify(synth=self, index=index)
		else:
			assert index == 0
			synthDriverHandler.synthDoneSpeaking.notify(synth=self)

	def _handleRemoteDriverChange(self):
		super()._handleRemoteDriverChange()
		synthDriverHandler.changeVoice(self, None)


SynthDriver = remoteSynthDriver
