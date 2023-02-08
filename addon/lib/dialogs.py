import wx
import addonHandler
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
import config
from .configuration import CONFIG_SECTION_NAME, OperatingMode, OPERATING_MODE_SETTING_NAME


addonHandler.initTranslation()


class NvdaRDSettingsPanel(SettingsPanel):
	title = _("NVDA Remote Desktop")

	def makeSettings(self, settingsSizer):
		sizer_helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: The label for a setting in NVDA RD settings to set operating mode.
		operatingModeText = _("Use NVDA RD for")
		operatingModeChoices = [i.displayString for i in OperatingMode]
		self.operatingModeList = sizer_helper.addLabeledControl(
			operatingModeText,
			wx.Choice,
			choices=operatingModeChoices,
		)
		self.operatingModeList.Selection = config.conf[CONFIG_SECTION_NAME][OPERATING_MODE_SETTING_NAME] - 1

	def onSave(self):
		config.conf[CONFIG_SECTION_NAME][OPERATING_MODE_SETTING_NAME] = self.operatingModeList.Selection + 1
