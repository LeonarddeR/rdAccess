import typing
import addonHandler
import synthDriverHandler
import queueHandler
from hwIo import boolToByte
import sys
import tones
import nvwave
from typing import Optional


if typing.TYPE_CHECKING:
	from ..lib import driver
	from ..lib import protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class remoteSynthDriver(driver.RemoteDriver, synthDriverHandler.SynthDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote speech")
	supportedNotifications = {synthDriverHandler.synthIndexReached, synthDriverHandler.synthDoneSpeaking}
	driverType = protocol.DriverType.SPEECH

	def __init__(self, port="auto"):
		super().__init__(port)
		tones.decide_beep.register(self.handle_decideBeep)
		nvwave.decide_playWaveFile.register(self.handle_decidePlayWaveFile)

	def terminate(self):
		tones.decide_beep.unregister(self.handle_decideBeep)
		nvwave.decide_playWaveFile.unregister(self.handle_decidePlayWaveFile)
		super().terminate()

	def handle_decideBeep(self, **kwargs):
		self.writeMessage(protocol.SpeechCommand.BEEP, self._pickle(kwargs))
		return False

	def handle_decidePlayWaveFile(self, **kwargs):
		self.writeMessage(protocol.SpeechCommand.PLAY_WAVE_FILE, self._pickle(kwargs))
		return False

	def _handleRemoteDisconnect(self):
		queueHandler.queueFunction(queueHandler.eventQueue, synthDriverHandler.findAndSetNextSynth, self.name)

	def speak(self, speechSequence):
		self.writeMessage(protocol.SpeechCommand.SPEAK, self._pickle(speechSequence))

	def cancel(self):
		self.writeMessage(protocol.SpeechCommand.CANCEL)

	def pause(self, switch):
		self.writeMessage(protocol.SpeechCommand.PAUSE, boolToByte(switch))

	@protocol.attributeReceiver(protocol.SpeechAttribute.SUPPORTED_COMMANDS, defaultValue=frozenset())
	def _incoming_supportedCommands(self, payLoad: bytes) -> frozenset:
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	def _get_supportedCommands(self):
		return self.getRemoteAttribute(protocol.SpeechAttribute.SUPPORTED_COMMANDS, allowCache=True)

	@protocol.attributeReceiver(protocol.SpeechAttribute.LANGUAGE, defaultValue=None)
	def _incoming_language(self, payload: bytes) -> Optional[str]:
		assert len(payload) > 0
		return self._unpickle(payload)

	def _get_language(self):
		return self.getRemoteAttribute(protocol.SpeechAttribute.LANGUAGE, allowCache=True)

	@protocol.commandHandler(protocol.SpeechCommand.INDEX_REACHED)
	def _command_indexReached(self, incomingPayload: bytes):
		assert len(incomingPayload) == 2
		index = int.from_bytes(incomingPayload, sys.byteorder)
		synthDriverHandler.synthIndexReached.notify(synth=self, index=index)

	def initSettings(self):
		# Call change voice to ensure the settings ring is updated.
		synthDriverHandler.changeVoice(self, None)
		return super().initSettings()


SynthDriver = remoteSynthDriver
