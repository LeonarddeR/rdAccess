from ._remoteHandler import RemoteHandler
import typing
import synthDriverHandler
from speech.commands import IndexCommand
import sys
import tones
import nvwave

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteSpeechHandler(RemoteHandler):
	driverType = protocol.DriverType.SPEECH
	_driver: synthDriverHandler.SynthDriver

	def __init__(self, pipeAddress: str):
		self._indexesSpeaking = []
		synthDriverHandler.synthIndexReached.register(self._onSynthIndexReached)
		synthDriverHandler.synthDoneSpeaking.register(self._onSynthDoneSpeaking)
		super().__init__(pipeAddress)

	def terminate(self):
		super().terminate()
		synthDriverHandler.synthDoneSpeaking.unregister(self._onSynthDoneSpeaking)
		synthDriverHandler.synthIndexReached.unregister(self._onSynthIndexReached)

	def _get__driver(self):
		return synthDriverHandler.getSynth()

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_COMMANDS)
	def _outgoing_supportedCommands(self) -> bytes:
		return self._pickle(self._driver.supportedCommands)

	@protocol.attributeSender(protocol.SpeechAttribute.LANGUAGE)
	def _outgoing_language(self) -> bytes:
		return self._pickle(self._driver.language)

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _command_speak(self, payload: bytes):
		sequence = self._unpickle(payload)
		for item in sequence:
			if isinstance(item, IndexCommand):
				item.index += protocol.speech.SPEECH_INDEX_OFFSET
				self._indexesSpeaking.append(item.index)
		# Queue speech to the current synth directly because we don't want unnecessary processing to happen.
		self._queueFunctionOnMainThread(self._driver.speak, sequence)

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _command_cancel(self, payload: bytes = b''):
		self._indexesSpeaking.clear()
		self._queueFunctionOnMainThread(self._driver.cancel)

	@protocol.commandHandler(protocol.SpeechCommand.PAUSE)
	def _command_pause(self, payload: bytes):
		assert len(payload) == 1
		switch = bool.from_bytes(payload, sys.byteorder)
		self._queueFunctionOnMainThread(self._driver.pause, switch)

	@protocol.commandHandler(protocol.SpeechCommand.BEEP)
	def _command_beep(self, payload: bytes):
		kwargs = self._unpickle(payload)
		self._queueFunctionOnMainThread(tones.beep, **kwargs)

	@protocol.commandHandler(protocol.SpeechCommand.PLAY_WAVE_FILE)
	def _command_playWaveFile(self, payload: bytes):
		kwargs = self._unpickle(payload)
		nvwave.playWaveFile(**kwargs)

	def _onSynthIndexReached(
			self,
			synth: typing.Optional[synthDriverHandler.SynthDriver] = None,
			index: typing.Optional[int] = None
	):
		assert synth == self._driver
		if index in self._indexesSpeaking:
			subtractedIndex = index - protocol.speech.SPEECH_INDEX_OFFSET
			indexBytes = subtractedIndex.to_bytes(
				length=2,  # Bytes needed to encode speech._manager.MAX_INDEX
				byteorder=sys.byteorder,  # for a single byte big/little endian does not matter.
				signed=False
			)
			self.writeMessage(protocol.SpeechCommand.INDEX_REACHED, indexBytes)

	def _onSynthDoneSpeaking(self, synth: typing.Optional[synthDriverHandler.SynthDriver] = None):
		self._indexesSpeaking.clear()

	def event_gainFocus(self, obj):
		super().event_gainFocus(obj)
		self._get_hasFocus()
