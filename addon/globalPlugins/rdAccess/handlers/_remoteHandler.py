# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0 or later

import os.path
import typing
from abc import abstractmethod

import addonHandler
import api
import globalVars
import keyboardHandler
import nvwave
import speech
import ui
import winUser
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
DriverT = typing.TypeVar("DriverT", bound=Driver)
_MISSING = object()


class RemoteHandler[DriverT: Driver](protocol.RemoteProtocolHandler[namedPipe.NamedPipeClient]):
	decide_remoteDisconnect: AccumulatingDecider
	_isSecureDesktopHandler: bool = False
	_remoteSessionhasFocus: bool | None = None
	_driver: DriverT
	_abstract__driver = True

	def _get__driver(self) -> DriverT:
		raise NotImplementedError

	def __new__(cls, *args, **kwargs):
		obj = super().__new__(cls, *args, **kwargs)
		obj.decide_remoteDisconnect = AccumulatingDecider(defaultDecision=False)
		return obj

	def initIo(
		self,
		ioThread: IoThread,
		pipeName: str,
	):
		self._dev = namedPipe.NamedPipeClient(
			pipeName=pipeName,
			onReceive=self._onReceive,
			onReadError=self._onReadError,
			ioThread=ioThread,
		)

	def __init__(
		self,
		ioThread: IoThread,
		pipeName: str,
	):
		super().__init__()
		self._pendingSettings: protocol.PendingValueStore[protocol.AttributeT, typing.Any] = (
			protocol.PendingValueStore()
		)
		self.initIo(ioThread, pipeName)

		self._onConnected(True)

	def _onConnected(self, connected: bool = True):
		if connected:
			self.pushProtocolVersion()
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
			nvwave.playWaveFile(wavePath)

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
		self._applyRemoteCapsLockToggle()

	@protocol.attributeSender(protocol.GenericAttribute.SUPPORTED_SETTINGS)
	def _outgoing_supportedSettings(self, settings=None):
		if not configuration.getDriverSettingsManagement():
			return []
		if settings is None:
			settings = self._driver.supportedSettings
		return settings

	@protocol.attributeSender("available*s")
	def _outgoing_availableSettingValues(self, attribute: protocol.AttributeT):
		if not configuration.getDriverSettingsManagement():
			return {}
		return getattr(self._driver, attribute)

	_incoming_setting = protocol.AttributeReceiver(protocol.SETTING_ATTRIBUTE_PREFIX + "*")

	@_incoming_setting.updateCallback
	def _queueIncomingSettingOnDriver(self, attribute: protocol.AttributeT, value: typing.Any):
		if not configuration.getDriverSettingsManagement():
			return
		if self._pendingSettings.push(attribute, value):
			self._queueFunctionOnMainThread(self._applyPendingSettings)

	def _applyPendingSettings(self):
		self._pendingSettings.drain(self._setIncomingSettingOnDriver)

	def _setIncomingSettingOnDriver(self, attribute: protocol.AttributeT, value: typing.Any):
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX) :]
		setattr(self._driver, name, value)

	@protocol.attributeSender(protocol.SETTING_ATTRIBUTE_PREFIX + "*")
	def _outgoing_setting(self, attribute: protocol.AttributeT):
		if not configuration.getDriverSettingsManagement():
			return None
		pending = self._pendingSettings.get(attribute, _MISSING)
		if pending is not _MISSING:
			return pending
		name = attribute[len(protocol.SETTING_ATTRIBUTE_PREFIX) :]
		return getattr(self._driver, name)

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

	_incoming_timeSinceInput = protocol.AttributeReceiver(
		protocol.GenericAttribute.TIME_SINCE_INPUT,
		defaultValue=False,
	)

	@_incoming_timeSinceInput.updateCallback
	def _post_timeSinceInput(self, attribute: protocol.AttributeT, value: int):
		assert attribute == protocol.GenericAttribute.TIME_SINCE_INPUT
		self._remoteSessionhasFocus = value <= MAX_TIME_SINCE_INPUT_FOR_REMOTE_SESSION_FOCUS
		if self._remoteSessionhasFocus:
			self._handleRemoteSessionGainFocus()

	def _handleRemoteSessionGainFocus(self):
		return

	_incoming_capsLockToggle = protocol.AttributeReceiver(
		protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
		defaultValue=None,
	)

	@_incoming_capsLockToggle.updateCallback
	def _post_capsLockToggle(self, attribute: protocol.AttributeT, _value: bool):
		assert attribute == protocol.GenericAttribute.CAPS_LOCK_TOGGLE
		self._queueFunctionOnMainThread(self._applyRemoteCapsLockToggle)

	def _applyRemoteCapsLockToggle(self):
		"""Aligns the local caps lock toggle state with the state last pushed by the server.

		Runs only while the remote session does not have focus; otherwise application is
		deferred to the next focus change.
		"""
		value = self._attributeValueProcessor.getValue(
			protocol.GenericAttribute.CAPS_LOCK_TOGGLE,
			fallBackToDefault=True,
		)
		if value is None or self._remoteProcessHasFocus:
			return
		if bool(winUser.getKeyState(winUser.VK_CAPITAL) & 1) != bool(value):
			keyboardHandler.KeyboardInputGesture.fromName("capsLock").send()

	def _onReadError(self, error: int) -> bool:
		return self.decide_remoteDisconnect.decide(handler=self, error=error)

	@abstractmethod
	# driver is positional-only: subclasses rename it (display/synth) to match the keyword
	# used by the braille.displayChanged / synthChanged extension points they register with.
	def _handleDriverChanged(self, driver: DriverT, /):
		self._attributeSenderStore(
			protocol.GenericAttribute.SUPPORTED_SETTINGS,
			settings=driver.supportedSettings,
		)

	def terminate(self):
		if not self._isSecureDesktopHandler:
			self._onConnected(False)
		super().terminate()
