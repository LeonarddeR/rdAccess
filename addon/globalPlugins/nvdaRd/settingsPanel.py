import wx
import addonHandler
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
import config
from .configuration import (
    CONFIG_SECTION_NAME,
    OperatingMode,
    OPERATING_MODE_SETTING_NAME,
    PERSISTENT_REGISTRATION_SETTING_NAME
)
from extensionPoints import Action
from typing import Union


addonHandler.initTranslation()


class NvdaRDSettingsPanel(SettingsPanel):
	title = _("Remote Desktop")
	post_onSave = Action()

	def makeSettings(self, settingsSizer):
		sizer_helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: The label for a setting in NVDA RD settings to set operating mode.
		operatingModeText = _("Use NVDA RD for")
		operatingModeChoices = [
			f"&{i.displayString}"
			for i in OperatingMode
		]
		self.operatingModeRadioBox = sizer_helper.addItem(
			wx.RadioBox(
				self,
				label=			operatingModeText,
				choices=operatingModeChoices
			)
		)
		self.operatingModeRadioBox.Selection = config.conf[CONFIG_SECTION_NAME][OPERATING_MODE_SETTING_NAME] - 1
		self.operatingModeRadioBox.Bind(wx.EVT_RADIOBOX, self.onoperatingModeChange)
		if config.isInstalledCopy():
			# Translators: The label for a setting in NVDA RD settings to enable
			# persistent registration of RD Pipe to the Windows registry.
			persistentRegistrationText = _("&Persist remote desktop client support when exiting NVDA")
			self.persistentRegistrationCheckbox = sizer_helper.addItem(
				wx.CheckBox(
				self,
				label=persistentRegistrationText
			))
			self.persistentRegistrationCheckbox.Value = config.conf[CONFIG_SECTION_NAME][PERSISTENT_REGISTRATION_SETTING_NAME]
			self.onoperatingModeChange(self.operatingModeRadioBox)

	def onoperatingModeChange(self, evt: Union[wx.CommandEvent, wx.RadioBox]):
		self.persistentRegistrationCheckbox.Enable(OperatingMode(evt.Selection + 1) & OperatingMode.CLIENT)

	def onSave(self):
		config.conf[CONFIG_SECTION_NAME][OPERATING_MODE_SETTING_NAME] = self.operatingModeRadioBox.Selection + 1
		config.conf[CONFIG_SECTION_NAME][PERSISTENT_REGISTRATION_SETTING_NAME] = (
			self.persistentRegistrationCheckbox.IsChecked()
			and bool(OperatingMode(self.operatingModeRadioBox.Selection + 1) & OperatingMode.CLIENT)
		)
		self.post_onSave.notify()
