import typing
import addonHandler
import synthDriverHandler
from hwIo import boolToByte
import sys
import tones
import nvwave
from typing import Optional
from extensionPoints import Action
from logHandler import log
from . import synthThread
from languageHandler import getLanguage

if typing.TYPE_CHECKING:
	from ...lib import driver
	from ...lib import protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	driver = addon.loadModule("lib.driver")
	protocol = addon.loadModule("lib.protocol")


class remoteSynthDriver(driver.RemoteDriver, synthDriverHandler.SynthDriver):
	# Translators: Name for a remote braille display.
	description = _("Remote speech")
	supportedNotifications = {synthDriverHandler.synthIndexReached, synthDriverHandler.synthDoneSpeaking}
	driverType = protocol.DriverType.SPEECH
	synthRemoteDisconnected = Action()
	__everInitialized: bool = False

	@classmethod
	def _handleFirstInit(cls):
		if cls.__everInitialized:
			return
		synthThread.initialize()
		cls.__everInitialized = True

	def __init__(self, port="auto"):
		self._handleFirstInit()
		super().__init__(port)
		nvwave.decide_playWaveFile.register(self.handle_decidePlayWaveFile)
		tones.decide_beep.register(self.handle_decideBeep)

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
		self.synthRemoteDisconnected.notify(synth=self)

	def speak(self, speechSequence):
		self.writeMessage(protocol.SpeechCommand.SPEAK, self._pickle(speechSequence))

	def cancel(self):
		try:
			self.writeMessage(protocol.SpeechCommand.CANCEL)
		except WindowsError:
			log.error("Error cancelling speech", exc_info=True)

	def pause(self, switch):
		self.writeMessage(protocol.SpeechCommand.PAUSE, boolToByte(switch))

	@protocol.attributeReceiver(protocol.SpeechAttribute.SUPPORTED_COMMANDS, defaultValue=frozenset())
	def _incoming_supportedCommands(self, payLoad: bytes) -> frozenset:
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	def _get_supportedCommands(self):
		attribute = protocol.SpeechAttribute.SUPPORTED_COMMANDS
		value = self._attributeValueProcessor.getValue(attribute, fallBackToDefault=True)
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
		synthDriverHandler.synthIndexReached.notify(synth=self, index=index)

	def initSettings(self):
		super().initSettings()
		# Queue change voice to the main thread to ensure the settings ring is updated.
		self._queueFunctionOnMainThread(synthDriverHandler.changeVoice, self, None)


SynthDriver = remoteSynthDriver
