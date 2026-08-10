# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import typing

import nvwave
import speech
import synthDriverHandler
import tones
from hwIo.ioThread import IoThread
from logHandler import log
from speech.commands import PitchCommand
from speech.extensions import speechCanceled
from speech.priorities import Spri
from speech.types import SpeechSequence

from ._remoteHandler import RemoteHandler

if typing.TYPE_CHECKING:
	from ....lib import configuration, protocol
else:
	import addonHandler

	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	protocol = addon.loadModule("lib.protocol")


class RemoteSpeechHandler(RemoteHandler[synthDriverHandler.SynthDriver]):
	driverType = protocol.DriverType.SPEECH

	def __init__(self, ioThread: IoThread, pipeName: str):
		super().__init__(ioThread, pipeName)
		speechCanceled.register(self._notifyDoneSpeaking)
		synthDriverHandler.synthChanged.register(self._handleDriverChanged)

	def terminate(self):
		synthDriverHandler.synthChanged.unregister(self._handleDriverChanged)
		speechCanceled.unregister(self._notifyDoneSpeaking)
		super().terminate()

	def _get__driver(self):
		synth = synthDriverHandler.getSynth()
		assert synth is not None
		return synth

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_COMMANDS)
	def _outgoing_supportedCommands(self, commands=None):
		if commands is None:
			commands = self._driver.supportedCommands
		return commands

	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self, language: str | None = None) -> str | None:
		if language is None:
			language = self._driver.language
		return language

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_LANGUAGES)
	def _outgoing_supportedLanguages(
		self,
		languages: list[str | None] | None = None,
	) -> list[str | None]:
		if languages is None:
			languages = self._getSupportedLanguages(self._driver)
		return languages

	@staticmethod
	def _getSupportedLanguages(synth: synthDriverHandler.SynthDriver) -> list[str | None]:
		try:
			languages = synth.availableLanguages
		except NotImplementedError:
			languages = {synth.language}
		return protocol.speech.encodeSupportedLanguages(languages)

	@protocol.commandHandler(protocol.RdMessageType.SPEAK)
	def _command_speak(self, sequence: SpeechSequence):
		self._queueFunctionOnMainThread(self._speak, sequence, _immediate=True)

	def _speak(self, sequence: SpeechSequence):
		pitchChange = configuration.getIncomingSpeechPitchChange(fromCache=True)
		if pitchChange != 0 and PitchCommand in self._driver.supportedCommands:
			sequence = [PitchCommand(offset=pitchChange), *sequence, PitchCommand()]
		sequence = protocol.speech.remapIndexesToCallbacks(sequence, self._sendIndex)
		assert speech.speech._speechState is not None
		speech.speech._speechState.isPaused = False
		speech.speech._speechState.beenCanceled = False
		speech.speech._manager.speak(sequence, priority=Spri.NORMAL)

	def _sendIndex(self, index: int):
		try:
			self.sendMessage(protocol.RdMessageType.INDEX, index=index)
		except OSError:
			log.warning("Error sending index", exc_info=True)

	def _notifyDoneSpeaking(self):
		self._sendIndex(0)

	@protocol.commandHandler(protocol.RdMessageType.CANCEL)
	def _command_cancel(self):
		self._queueFunctionOnMainThread(self._cancel, _immediate=True)

	def _cancel(self):
		speech.speech._manager.cancel()
		assert speech.speech._speechState is not None
		speech.speech._speechState.beenCanceled = True
		speech.speech._speechState.isPaused = False

	@protocol.commandHandler(protocol.RdMessageType.PAUSE_SPEECH)
	def _command_pause(self, switch: bool):
		self._queueFunctionOnMainThread(self._pause, switch, _immediate=True)

	def _pause(self, switch: bool):
		speech.pauseSpeech(switch)

	@protocol.commandHandler(protocol.RdMessageType.TONE)
	def _command_beep(self, **kwargs):
		log.debug(f"Received TONE command: {kwargs}")
		# Tones are always asynchronous
		tones.beep(**kwargs)

	@protocol.commandHandler(protocol.RdMessageType.WAVE)
	def _command_playWaveFile(self, **kwargs):
		log.debug(f"Received WAVE command: {kwargs}")
		# Ensure the wave plays asynchronous.
		kwargs["asynchronous"] = True
		nvwave.playWaveFile(**kwargs)

	def _handleDriverChanged(self, synth: synthDriverHandler.SynthDriver):
		self._notifyDoneSpeaking()
		super()._handleDriverChanged(synth)
		self._attributeSenderStore(
			protocol.SpeechAttribute.SUPPORTED_COMMANDS,
			commands=synth.supportedCommands,
		)
		self._attributeSenderStore(protocol.SpeechAttribute.LANGUAGE, language=synth.language)
		self._attributeSenderStore(
			protocol.SpeechAttribute.SUPPORTED_LANGUAGES,
			languages=self._getSupportedLanguages(synth),
		)
