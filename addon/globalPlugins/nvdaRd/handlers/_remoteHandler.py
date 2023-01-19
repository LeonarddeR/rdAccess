import typing
import addonHandler
import sys
import api
import time
import keyboardHandler

if typing.TYPE_CHECKING:
	from .. import protocol
	from .. import namedPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	protocol = addon.loadModule("lib.protocol")
	namedPipe = addon.loadModule("lib.namedPipe")


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipe
	_focusLastSet: float
	_focusTestGesture = keyboardHandler.KeyboardInputGesture.fromName("alt+control+shift+f24")

	def __init__(self, driverType: protocol.DriverType, pipeAddress: str):
		super().__init__(driverType)
		self._focusLastSet = time.time()
		try:
			self._dev = namedPipe.NamedPipe(pipeAddress, onReceive=self._onReceive, onReadError=self._onReadError)
		except EnvironmentError:
			raise

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

	_cache_hasFocus = True

	def _get_hasFocus(self):
		remoteProcessHasFocus = api.getFocusObject().processID == self._dev.serverProcessId
		if not remoteProcessHasFocus:
			return False
		valueProcessor = self._attributeValueProcessors[protocol.GenericAttribute.HAS_FOCUS]
		if valueProcessor.hasNewValueSince(self._focusLastSet):
			return valueProcessor.value
		# Request an attribute update for next round
		self._focusLastSet = time.time()
		# Tell the remote system to intercept a incoming gesture.
		self.writeMessage(
			protocol.GenericCommand.INTERCEPT_GESTURE,
			self.pickle(self._focusTestGesture.normalizedIdentifiers)
		)
		self.REQUESTRemoteAttribute(protocol.GenericAttribute.HAS_FOCUS)
		self._focusTestGesture.send()
		return False

	@protocol.attributeReceiver(protocol.GenericAttribute.HAS_FOCUS, defaultValue=False)
	def _handleHasFocus(self, payload: bytes) -> bool:
		assert len(payload) == 1
		return bool.from_bytes(payload, byteorder=sys.byteorder)
