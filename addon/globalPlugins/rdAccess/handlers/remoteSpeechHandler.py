# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import sys
import typing

import nvwave
import speech
import synthDriverHandler
import tones
from hwIo.ioThread import IoThread
from logHandler import log
from speech.commands import IndexCommand
from speech.types import SpeechSequence

from ._remoteHandler import RemoteHandler

if typing.TYPE_CHECKING:
	from ....lib import protocol
else:
	import addonHandler

	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteSpeechHandler(RemoteHandler[synthDriverHandler.SynthDriver]):
	driverType = protocol.DriverType.SPEECH

	def __init__(self, ioThread: IoThread, pipeName: str):
		self._indexesSpeaking = []
		super().__init__(ioThread, pipeName)
		synthDriverHandler.synthIndexReached.register(self._onSynthIndexReached)
		synthDriverHandler.synthDoneSpeaking.register(self._onSynthDoneSpeaking)
		synthDriverHandler.synthChanged.register(self._handleDriverChanged)

	def terminate(self):
		synthDriverHandler.synthChanged.unregister(self._handleDriverChanged)
		synthDriverHandler.synthDoneSpeaking.unregister(self._onSynthDoneSpeaking)
		synthDriverHandler.synthIndexReached.unregister(self._onSynthIndexReached)
		super().terminate()

	def _get__driver(self):
		return synthDriverHandler.getSynth()

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_COMMANDS)
	def _outgoing_supportedCommands(self, commands=None) -> bytes:
		if commands is None:
			commands = self._driver.supportedCommands
		return self._pickle(commands)

	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self, language: str | None = None) -> bytes:
		if language is None:
			language = self._driver.language
		return self._pickle(language)

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _command_speak(self, payload: bytes):
		sequence = self._unpickle(payload)
		self._queueFunctionOnMainThread(self._speak, sequence)

	def _speak(self, sequence: SpeechSequence):
		for item in sequence:
			if isinstance(item, IndexCommand):
				item.index += protocol.speech.SPEECH_INDEX_OFFSET
				self._indexesSpeaking.append(item.index)
		# Send speech to the current synth directly because we don't want unnecessary processing to happen.
		# We need to change speech state accordingly.
		speech.speech._speechState.isPaused = False
		speech.speech._speechState.beenCanceled = False
		self._driver.speak(sequence)

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _command_cancel(self, _payload: bytes = b""):
		self._indexesSpeaking.clear()
		self._queueFunctionOnMainThread(self._cancel)

	def _cancel(self):
		self._driver.cancel()
		speech.speech._speechState.beenCanceled = True
		speech.speech._speechState.isPaused = False

	@protocol.commandHandler(protocol.SpeechCommand.PAUSE)
	def _command_pause(self, payload: bytes):
		assert len(payload) == 1
		switch = bool.from_bytes(payload, sys.byteorder)
		self._queueFunctionOnMainThread(self._pause, switch)

	def _pause(self, switch: bool):
		speech.pauseSpeech(switch)

	@protocol.commandHandler(protocol.SpeechCommand.BEEP)
	def _command_beep(self, payload: bytes):
		kwargs = self._unpickle(payload)
		log.debug(f"Received BEEP command: {kwargs}")
		# Tones are always asynchronous
		tones.beep(**kwargs)

	@protocol.commandHandler(protocol.SpeechCommand.PLAY_WAVE_FILE)
	def _command_playWaveFile(self, payload: bytes):
		kwargs = self._unpickle(payload)
		log.debug(f"Received PLAY_WAVE_FILE command: {kwargs}")
		# Ensure the wave plays asynchronous.
		kwargs["asynchronous"] = True
		nvwave.playWaveFile(**kwargs)

	def _onSynthIndexReached(
		self,
		synth: synthDriverHandler.SynthDriver | None = None,
		index: int | None = None,
	):
		assert synth == self._driver
		if index in self._indexesSpeaking:
			subtractedIndex = index - protocol.speech.SPEECH_INDEX_OFFSET
			indexBytes = subtractedIndex.to_bytes(
				length=2,  # Bytes needed to encode speech._manager.MAX_INDEX
				byteorder=sys.byteorder,  # for a single byte big/little endian does not matter.
				signed=False,
			)
			try:
				self.writeMessage(protocol.SpeechCommand.INDEX_REACHED, indexBytes)
			except OSError:
				log.warning("Error calling _onSynthIndexReached", exc_info=True)
			self._indexesSpeaking.remove(index)

	def _onSynthDoneSpeaking(self, synth: synthDriverHandler.SynthDriver | None = None):
		assert synth == self._driver
		if len(self._indexesSpeaking) > 0:
			self._indexesSpeaking.clear()
			try:
				self.writeMessage(protocol.SpeechCommand.INDEX_REACHED, b"\x00\x00")
			except OSError:
				log.warning("Error calling _onSynthDoneSpeaking", exc_info=True)

	def _handleDriverChanged(self, synth: synthDriverHandler.SynthDriver):
		self._indexesSpeaking.clear()
		super()._handleDriverChanged(synth)
		self._attributeSenderStore(
			protocol.SpeechAttribute.SUPPORTED_COMMANDS,
			commands=synth.supportedCommands,
		)
		self._attributeSenderStore(protocol.SpeechAttribute.LANGUAGE, language=synth.language)
