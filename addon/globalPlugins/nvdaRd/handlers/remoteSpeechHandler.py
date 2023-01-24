from ._remoteHandler import RemoteHandler
import typing
import synthDriverHandler
from speech.commands import IndexCommand
import sys

if typing.TYPE_CHECKING:
	from .. import protocol
else:
	import addonHandler
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")


class RemoteSpeechHandler(RemoteHandler):
	driverType = protocol.DriverType.SPEECH

	def __init__(self, pipeAddress: str):
		self._indexesSpeaking = []
		synthDriverHandler.synthIndexReached.register(self._onSynthIndexReached)
		synthDriverHandler.synthDoneSpeaking.register(self._onSynthDoneSpeaking)
		super().__init__(pipeAddress)

	def terminate(self):
		synthDriverHandler.synthDoneSpeaking.unregister(self._onSynthDoneSpeaking)
		synthDriverHandler.synthIndexReached.unregister(self._onSynthIndexReached)
		return super().terminate()

	_curSynth: synthDriverHandler.SynthDriver

	def _get__curSynth(self):
		return synthDriverHandler.getSynth()

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_COMMANDS)
	def _sendSupportedCommands(self) -> bytes:
		return self._pickle(self._curSynth.supportedCommands)

	@protocol.attributeSender(protocol.SpeechAttribute.SUPPORTED_SETTINGS)
	def _sendSupportedSettings(self) -> bytes:
		return self._pickle(self._curSynth.supportedSettings)

	@protocol.commandHandler(protocol.SpeechCommand.SPEAK)
	def _handleSpeak(self, payload: bytes):
		sequence = self._unpickle(payload)
		for item in sequence:
			if isinstance(item, IndexCommand):
				self._indexesSpeaking.append(item.index)
		# Queue speech to the current synth directly because we don't want unnecessary processing to happen.
		self._curSynth.speak(sequence)

	@protocol.commandHandler(protocol.SpeechCommand.CANCEL)
	def _handleCancel(self, payload: bytes = b''):
		self._indexesSpeaking.clear()
		self._curSynth.cancel()

	@protocol.commandHandler(protocol.SpeechCommand.PAUSE)
	def _handlePause(self, payload: bytes):
		assert len(payload) == 1
		switch = bool.from_bytes(payload, sys.byteorder)
		self._curSynth.pause(switch)

	def _onSynthIndexReached(
		self,
		synth: typing.Optional[synthDriverHandler.SynthDriver] = None,
		index: typing.Optional[int] = None
	):
		assert synth == self._curSynth
		if index in self._indexesSpeaking:
			indexBytes = typing.cast(int, index).to_bytes(
				length=2,  # Bytes needed to encode speech._manager.MAX_INDEX
				byteorder=sys.byteorder,  # for a single byte big/little endian does not matter.
				signed=False
			)
			self.writeMessage(protocol.SpeechCommand.INDEX_REACHED, indexBytes)

	def _onSynthDoneSpeaking(self, synth: typing.Optional[synthDriverHandler.SynthDriver] = None):
		self._indexesSpeaking.clear()
