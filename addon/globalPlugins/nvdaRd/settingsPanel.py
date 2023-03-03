import wx
import addonHandler
from gui import guiHelper, messageBox
from gui.settingsDialogs import SettingsPanel
import config
from .configuration import (
    CONFIG_SECTION_NAME,
    OperatingMode,
    OPERATING_MODE_SETTING_NAME,
    PERSISTENT_REGISTRATION_SETTING_NAME,
    RECOVER_REMOTE_SPEECH_SETTING_NAME,
)
from extensionPoints import Action
import typing
from typing import Union

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

		# Translators: The label for a setting in NVDA RD settings to enable
		# automatic recovery of remote speech when the connection was lost.
		recoverRemoteSpeechText = _("Automatically &recover remote speech after connection loss")
		self.recoverRemoteSpeechCheckbox = sizer_helper.addItem(
			wx.CheckBox(
			self,
			label=recoverRemoteSpeechText
		))
		self.recoverRemoteSpeechCheckbox.Value = config.conf[CONFIG_SECTION_NAME][RECOVER_REMOTE_SPEECH_SETTING_NAME]

		# Translators: This is the label for a group of options in the
		# NVDA Remote Desktop settings panel
		rdpGroupText = _("Microsoft Remote Desktop")
		rdpGroupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=rdpGroupText)
		rdpGroupBox = rdpGroupSizer.GetStaticBox()
		rdpGroup = guiHelper.BoxSizerHelper(self, sizer=rdpGroupSizer)
		sizer_helper.addItem(rdpGroup)

		# Translators: The label for a setting in NVDA RD settings to enable
		# persistent registration of RD Pipe to the Windows registry.
		persistentRegistrationText = _("&Persist client support when exiting NVDA")
		self.persistentRegistrationCheckbox = rdpGroup.addItem(
			wx.CheckBox(
			rdpGroupBox ,
			label=persistentRegistrationText
		))
		self.persistentRegistrationCheckbox.Value = config.conf[CONFIG_SECTION_NAME][PERSISTENT_REGISTRATION_SETTING_NAME]
		self.persistentRegistrationCheckbox.Enable(config.isInstalledCopy())

		# Translators: This is the label for a group of options in the
		# NVDA Remote Desktop settings panel
		citrixGroupText = _("Citrix")
		citrixGroupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=citrixGroupText)
		citrixGroupBox = citrixGroupSizer.GetStaticBox()
		citrixGroup = guiHelper.BoxSizerHelper(self, sizer=citrixGroupSizer)
		sizer_helper.addItem(citrixGroup)

		# Translators: The label for a setting in NVDA RD settings to enable
		# Citrix support.
		citrixSupportText = _(
			"&Enable Citrix Workspace support "
			"(requires administrator privileges)"
		)
		self.citrixSupportCheckbox = rdpGroup.addItem(
			wx.CheckBox(
			citrixGroupBox ,
			label=citrixSupportText
		))
		self.citrixSupportCheckbox.Value = rdPipe.isCitrixSupportRegistered()
		self.citrixSupportCheckbox.Enable(config.isInstalledCopy())

		self.onoperatingModeChange(self.operatingModeRadioBox)

	def onCitrixSupportChanged(self, value: bool):
		if value:
			if messageBox(
				# Translators: A message to warn the user when enabling Citrix support.
				_(
					"You are about to enable Citrix support for NVDA Remote desktop. "
					"Citrix support can only be enabled system wide, "
					"however the NVDA Remote Desktop add-on is installed under the current user context. "
					"You are discouraged to continue unless you are the only user of this system. "
					"Furthermore, this action requires administrative access. Are you sure you wish to proceed?"
				),
				# Translators: The title of the warning dialog displayed when enabling Citrix support
				_("Citrix Support Warning"),
				wx.YES | wx.NO | wx.ICON_WARNING,
				self
			) == wx.NO:
				return
		if not rdPipe.dllInstall(
			value,
			comServer=True,
			rdp=False,
			citrix=True,
			localMachine=True,
			architecture=rdPipe.Architecture.X86
		):
			messageBox(
				# Translators: The message displayed when Citrix registration failed.
				_("Enabling Citrix support failed.  Please check the Log Viewer for more information."),
				# Translators: The title of a dialog presented when Citrix registrartion failed.
				_("Citrix Support Error"),
				wx.OK | wx.ICON_ERROR,
				self
			)

	def onoperatingModeChange(self, evt: Union[wx.CommandEvent, wx.RadioBox]):
		self.persistentRegistrationCheckbox.Enable(OperatingMode(evt.Selection + 1) & OperatingMode.CLIENT)
		self.recoverRemoteSpeechCheckbox.Enable(OperatingMode(evt.Selection + 1) & OperatingMode.SERVER)

	def onSave(self):
		config.conf[CONFIG_SECTION_NAME][OPERATING_MODE_SETTING_NAME] = self.operatingModeRadioBox.Selection + 1
		config.conf[CONFIG_SECTION_NAME][RECOVER_REMOTE_SPEECH_SETTING_NAME] = self.recoverRemoteSpeechCheckbox.IsChecked()
		config.conf[CONFIG_SECTION_NAME][PERSISTENT_REGISTRATION_SETTING_NAME] = (
			self.persistentRegistrationCheckbox.IsChecked()
			and bool(OperatingMode(self.operatingModeRadioBox.Selection + 1) & OperatingMode.CLIENT)
		)
		citrixEnabled = self.citrixSupportCheckbox.IsChecked()
		if citrixEnabled is not rdPipe.isCitrixSupportRegistered():
			self.onCitrixSupportChanged(citrixEnabled)

		self.post_onSave.notify()
