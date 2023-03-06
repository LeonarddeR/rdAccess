import wx
import addonHandler
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
import config
from . import configuration
from extensionPoints import Action
import typing

if typing.TYPE_CHECKING:
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	rdPipe = addon.loadModule("lib.rdPipe")
addonHandler.initTranslation()


class NvdaRDSettingsPanel(SettingsPanel):
	# Translators: The label for the NVDA Remote Desktop settings panel.
	title = _("Remote Desktop")
	post_onSave = Action()

	def makeSettings(self, settingsSizer):
		sizer_helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: The label for a setting in NVDA RD settings to set operating mode.
		operatingModeText = _("Use NVDA RD for")
		operatingModeChoices = [
			f"&{i.displayString}"
			for i in configuration.OperatingMode
		]
		self.operatingModeRadioBox = sizer_helper.addItem(
			wx.RadioBox(
				self,
				label=operatingModeText,
				choices=operatingModeChoices
			)
		)
		self.operatingModeRadioBox.Selection = int(configuration.getOperatingMode()) - 1
		self.operatingModeRadioBox.Bind(wx.EVT_RADIOBOX, self.onoperatingModeChange)

		# Translators: The label for a setting in NVDA RD settings to enable
		# automatic recovery of remote speech when the connection was lost.
		recoverRemoteSpeechText = _("&Automatically recover remote speech after connection loss")
		self.recoverRemoteSpeechCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=recoverRemoteSpeechText
		))
		self.recoverRemoteSpeechCheckbox.Value = configuration.getRecoverRemoteSpeech()

		# Translators: The label for a setting in NVDA RD settings to enable
		# persistent registration of RD Pipe to the Windows registry.
		persistentRegistrationText = _("&Persist client support when exiting NVDA")
		self.persistentRegistrationCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=persistentRegistrationText
		))
		self.persistentRegistrationCheckbox.Value = configuration.getPersistentRegistration()
		self.persistentRegistrationCheckbox.Enable(config.isInstalledCopy())

		# Translators: The label for a setting in NVDA RD settings to enable
		# registration of RD Pipe to the Windows registry for remote desktop support.
		remoteDesktopSupportText = _("Enable Microsoft &Remote Desktop support")
		self.remoteDesktopSupportCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=remoteDesktopSupportText
		))
		self.remoteDesktopSupportCheckbox.Value = configuration.getRemoteDesktopSupport()

		# Translators: The label for a setting in NVDA RD settings to enable
		# registration of RD Pipe to the Windows registry for Citrix support.
		citrixSupportText = _("Enable &Citrix Workspace support")
		self.citrixSupportCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=citrixSupportText
		))
		self.citrixSupportCheckbox.Value = configuration.getCitrixSupport()

		self.onoperatingModeChange(self.operatingModeRadioBox)

	def onoperatingModeChange(self, evt: typing.Union[wx.CommandEvent, wx.RadioBox]):
		isClient = configuration.OperatingMode(evt.Selection + 1) & configuration.OperatingMode.CLIENT
		self.persistentRegistrationCheckbox.Enable(isClient)
		self.remoteDesktopSupportCheckbox.Enable(isClient)
		self.citrixSupportCheckbox.Enable(isClient and rdPipe.isCitrixSupported())
		self.recoverRemoteSpeechCheckbox.Enable(configuration.OperatingMode(evt.Selection + 1) & configuration.OperatingMode.SERVER)

	def onSave(self):
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.OPERATING_MODE_SETTING_NAME] = self.operatingModeRadioBox.Selection + 1
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.RECOVER_REMOTE_SPEECH_SETTING_NAME] = self.recoverRemoteSpeechCheckbox.IsChecked()
		isClient = bool(configuration.OperatingMode(self.operatingModeRadioBox.Selection + 1) & configuration.OperatingMode.CLIENT)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.PERSISTENT_REGISTRATION_SETTING_NAME] = (
			self.persistentRegistrationCheckbox.IsChecked()
			and isClient
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.REMOTE_DESKTOP_SETTING_NAME] = (
			self.remoteDesktopSupportCheckbox.IsChecked()
			and isClient
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.CITRIX_SETTING_NAME] = (
			self.citrixSupportCheckbox.IsChecked()
			and isClient
			and rdPipe.isCitrixSupported()
		)

		self.post_onSave.notify()
