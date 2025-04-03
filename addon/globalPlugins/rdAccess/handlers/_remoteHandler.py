# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os.path
import sys
import typing
from abc import abstractmethod

import addonHandler
import api
import globalVars
import nvwave
import speech
import tones
import ui
import wx
from driverHandler import Driver
from extensionPoints import AccumulatingDecider
from hwIo.ioThread import IoThread
from logHandler import log

if typing.TYPE_CHECKING:
	from ....lib import configuration, namedPipe, protocol
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	namedPipe = addon.loadModule("lib.namedPipe")
	protocol = addon.loadModule("lib.protocol")


MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS = 200


class RemoteHandler(protocol.RemoteProtocolHandler):
	_dev: namedPipe.NamedPipeBase
	decide_remoteDisconnect: AccumulatingDecider
	_isSecureDesktopHandler: bool = False
	_remoteSessionhasFocus: bool | None = None
	_driver: Driver
	_abstract__driver = True

	def _get__driver(self) -> Driver:
		raise NotImplementedError

	def __new__(cls, *args, **kwargs):
		obj = super().__new__(cls, *args, **kwargs)
		obj.decide_remoteDisconnect = AccumulatingDecider(defaultDecision=False)
		return obj

	def initIo(
		self,
		ioThread: IoThread,
		pipeName: str,
		isNamedPipeClient: bool = True,
	):
		if isNamedPipeClient:
			self._dev = namedPipe.NamedPipeClient(
				pipeName=pipeName,
				onReceive=self._onReceive,
				onReadError=self._onReadError,
				ioThread=ioThread,
			)
		else:
			self._dev = namedPipe.NamedPipeServer(
				pipeName=pipeName,
				onReceive=self._onReceive,
				onConnected=self._onConnected,
				ioThreadEx=ioThread,
			)

	def __init__(
		self,
		ioThread: IoThread,
		pipeName: str,
		isNamedPipeClient: bool = True,
	):
		self._isSecureDesktopHandler = not isNamedPipeClient
		super().__init__()
		self.initIo(ioThread, pipeName, isNamedPipeClient)

		if not self._isSecureDesktopHandler:
			self._onConnected(True)
		elif self._remoteSessionhasFocus is None:
			self._remoteSessionhasFocus = False

	def _onConnected(self, connected: bool = True):
		if self._isSecureDesktopHandler:
			self._remoteSessionhasFocus = connected
		if connected:
			self._handleDriverChanged(self._driver)
		wx.CallAfter(self._handleNotifications, connected)

	def _handleNotifications(self, connected: bool):
		notifications = configuration.getConnectionNotifications()
		if notifications & configuration.ConnectionNotifications.MESSAGES:
			match self.driverType:
				case protocol.DriverType.SPEECH:
					# Translators: Translation of the connection type in connection messages
					driverTypeString = pgettext("connection type", "speech")
				case protocol.DriverType.BRAILLE:
					# Translators: Translation of the connection type in connection messages
					driverTypeString = pgettext("connection type", "braille")

			connectedString = (
				# Translators: Translation of the connection status in connection messages.
				_("connected")
				if connected
				# Translators: Translation of the connection status in connection messages.
				else _("disconnected")
			)
			# Translators: Translation of the connection message.
			# (E.g. "Remote braille/speech  connected/disconnected")
			msg = _("Remote {} {}").format(driverTypeString, connectedString)
			ui.message(msg, speechPriority=speech.speech.Spri.NEXT)
		if notifications & configuration.ConnectionNotifications.SOUNDS:
			wave = "connected" if connected else "disconnected"
			wavePath = os.path.join(globalVars.appDir, "waves", f"{wave}.wav")
			if os.path.isfile(wavePath):
				nvwave.playWaveFile(wavePath)
			else:
				hz = 550 if connected else 137.5
				tones.beep(hz, 100)

	def event_gainFocus(self, _obj):
		if self._isSecureDesktopHandler:
			return
		# Invalidate the property cache to ensure that hasFocus will be fetched again.
		# Normally, hasFocus should be cached since it is pretty expensive
		# and should never try to fetch the time since input from the remote driver
		# more than once per core cycle.
		# However, if we don't clear the cache here, the braille handler won't be enabled correctly
		# for the first focus outside the remote window.
		self.invalidateCache()
		self._remoteSessionhasFocus = None

	@protocol.attributeSender(protocol.GenericAttribute.SUPPORTED_SETTINGS)
	def _outgoing_supportedSettings(self, settings=None) -> bytes:
		if not configuration.getDriverSettingsManagement():
			return self._pickle([])
		if settings is None:
			settings = self._driver.supportedSettings
		return self._pickle(settings)

	@protocol.attributeSender(b"available*s")
	def _outgoing_availableSettingValues(self, attribute: protocol.AttributeT) -> bytes:
		if not configuration.getDriverSettingsManagement():
			return self._pickle({})
		name = attribute.decode("ASCII")
		return self._pickle(getattr(self._driver, name))

	@protocol.attributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _incoming_setting(self, _attribute: protocol.AttributeT, payLoad: bytes):
		assert len(payLoad) > 0
		return self._unpickle(payLoad)

	@_incoming_setting.updateCallback
	def _setIncomingSettingOnDriver(self, attribute: protocol.AttributeT, value: typing.Any):
		if not configuration.getDriverSettingsManagement():
			return
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX) :].decode("ASCII")
		setattr(self._driver, name, value)

	@protocol.attributeSender(protocol.SETTING_ATTRIBUTE_PREFIX + b"*")
	def _outgoing_setting(self, attribute: protocol.AttributeT):
		if not configuration.getDriverSettingsManagement():
			return self._pickle(None)
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX) :].decode("ASCII")
		return self._pickle(getattr(self._driver, name))

	_remoteProcessHasFocus: bool

	def _get__remoteProcessHasFocus(self):
		if self._isSecureDesktopHandler:
			self._remoteProcessHasFocus = True
			return self._remoteProcessHasFocus
		focus = api.getFocusObject()
		return focus.processID in (
			self._dev.pipeProcessId,
			self._dev.pipeParentProcessId,
		)

	hasFocus: bool

	def _get_hasFocus(self) -> bool:
		remoteProcessHasFocus = self._remoteProcessHasFocus
		if not remoteProcessHasFocus:
			return remoteProcessHasFocus
		if self._remoteSessionhasFocus is not None:
			return self._remoteSessionhasFocus
		log.debug("Requesting time since input from remote driver")
		attribute = protocol.GenericAttribute.TIME_SINCE_INPUT
		self.requestRemoteAttribute(attribute)
		return False

	@protocol.attributeReceiver(protocol.GenericAttribute.TIME_SINCE_INPUT, defaultValue=False)
	def _incoming_timeSinceInput(self, payload: bytes) -> int:
		assert len(payload) == 4
		return int.from_bytes(payload, byteorder=sys.byteorder, signed=False)

	@_incoming_timeSinceInput.updateCallback
	def _post_timeSinceInput(self, attribute: protocol.AttributeT, value: int):
		assert attribute == protocol.GenericAttribute.TIME_SINCE_INPUT
		self._remoteSessionhasFocus = value <= MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS
		if self._remoteSessionhasFocus:
			self._handleRemoteSessionGainFocus()

	def _handleRemoteSessionGainFocus(self):
		return

	def _onReadError(self, error: int) -> bool:
		return self.decide_remoteDisconnect.decide(handler=self, error=error)

	@abstractmethod
	def _handleDriverChanged(self, driver: Driver):
		self._attributeSenderStore(
			protocol.GenericAttribute.SUPPORTED_SETTINGS,
			settings=driver.supportedSettings,
		)

	def terminate(self):
		if not self._isSecureDesktopHandler:
			self._onConnected(False)
		super().terminate()
