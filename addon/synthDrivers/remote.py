import typing
import addonHandler
import synthDriverHandler
import queueHandler
from hwIo import boolToByte
import sys
from speech.commands import IndexCommand

if typing.TYPE_CHECKING:
	from ..lib.protocol import driver
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

	def _handleRemoteDisconnect(self):
		queueHandler.queueFunction(queueHandler.eventQueue, synthDriverHandler.findAndSetNextSynth, self.name)

	def speak(self, speechSequence):
		for item in speechSequence:
			if isinstance(item, IndexCommand):
				item.index += protocol.speech.SPEECH_INDEX_OFFSET
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
		return self._attributeValueProcessor.getValue(protocol.SpeechAttribute.SUPPORTED_COMMANDS)

	@protocol.commandHandler(protocol.SpeechCommand.INDEX_REACHED)
	def _command_indexReached(self, incomingPayload: bytes):
		assert len(incomingPayload) == 2
		index = int.from_bytes(incomingPayload, sys.byteorder)
		index -= protocol.speech.SPEECH_INDEX_OFFSET
		synthDriverHandler.synthIndexReached.notify(synth=self, index=index)


SynthDriver = remoteSynthDriver
