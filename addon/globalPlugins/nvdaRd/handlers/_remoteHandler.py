import typing
import addonHandler
import sys
import api
import time
import keyboardHandler
from logHandler import log
from enum import Enum, auto

if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


class RemoteFocusState(Enum):
	NONE = auto()
	CLIENT_FOCUSED = auto()
	SESSION_PENDING = auto()
	SESSION_FOCUSED = auto()


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipeBase
	_focusLastSet: float
	_focusTestGesture = keyboardHandler.KeyboardInputGesture.fromName("alt+control+shift+f24")

	def __init__(self, pipeName: str, isNamedPipeClient: bool = True):
		super().__init__()
		self._focusLastSet = time.time()
		try:
			IO = namedPipe.NamedPipeClient if isNamedPipeClient else namedPipe.NamedPipeServer
			self._dev = IO(pipeName=pipeName, onReceive=self._onReceive, onReadError=self._onReadError)
		except EnvironmentError:
			raise

		for handler in self._attributeSenders.values():
			handler()

	def _onReadError(self, error: int) -> bool:
		if error == 109:
			# Broken pipe error
			self.terminate()
			return True
		return False

	def terminate(self):
		# Make sure the device gets closed.
		self._dev.close()

	def event_gainFocus(self, obj):
		self._focusLastSet = time.time()

	hasFocus: RemoteFocusState
	_cache_hasFocus = True

	def _get_hasFocus(self) -> RemoteFocusState:
		remoteProcessHasFocus = api.getFocusObject().processID == self._dev.pipeProcessId
		if not remoteProcessHasFocus:
			return RemoteFocusState.NONE
		valueProcessor = self._attributeValueProcessors[protocol.GenericAttribute.HAS_FOCUS]
		log.debug("Requesting focus information from remote driver")
		if valueProcessor.hasNewValueSince(self._focusLastSet):
			newValue = valueProcessor.value
			log.debug(f"Focus value changed since focus last set, set to {newValue}")
			return RemoteFocusState.SESSION_FOCUSED if newValue else RemoteFocusState.CLIENT_FOCUSED
		# Request an attribute update for next round
		self._focusLastSet = time.time()
		# Tell the remote system to intercept a incoming gesture.
		log.debug("Instructing remote system to intercept gesture")
		self.writeMessage(
			protocol.GenericCommand.INTERCEPT_GESTURE,
			self._pickle(self._focusTestGesture.normalizedIdentifiers)
		)
		self.REQUESTRemoteAttribute(protocol.GenericAttribute.HAS_FOCUS)
		log.debug("Sending focus test gesture")
		self._focusTestGesture.send()
		return RemoteFocusState.SESSION_PENDING

	@protocol.attributeReceiver(protocol.GenericAttribute.HAS_FOCUS, defaultValue=False)
	def _handleHasFocus(self, payload: bytes) -> bool:
		assert len(payload) == 1
		return bool.from_bytes(payload, byteorder=sys.byteorder)
