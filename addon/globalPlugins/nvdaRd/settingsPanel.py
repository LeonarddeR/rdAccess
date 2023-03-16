import wx
import addonHandler
from gui import guiHelper, nvdaControls, messageBox
from gui.settingsDialogs import SettingsPanel
import config
from extensionPoints import Action
import typing
import functools
import operator

if typing.TYPE_CHECKING:
	from ...lib import configuration
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	rdPipe = addon.loadModule("lib.rdPipe")

addonHandler.initTranslation()


class NvdaRDSettingsPanel(SettingsPanel):
	# Translators: The label for the NVDA Remote Desktop settings panel.
	title = _("Remote Desktop")
	post_onSave = Action()

	def makeSettings(self, settingsSizer):
		sizer_helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: The label for a list of check boxes in NVDA RD settings to set operating mode.
		operatingModeText = _("&Enable NVDA RD for")
		operatingModeChoices = [i.displayString for i in configuration.OperatingMode]
		self.operatingModeList = sizer_helper.addLabeledControl(
			operatingModeText,
			nvdaControls.CustomCheckListBox,
			choices=operatingModeChoices
		)
		self.operatingModeList.CheckedItems = [
			n for n, e in enumerate(configuration.OperatingMode)
			if configuration.getOperatingMode() & e
		]
		self.operatingModeList.Select(0)
		self.operatingModeList.Bind(wx.EVT_CHECKLISTBOX, self.onoperatingModeChange)

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
		# support for exchanging driver settings between the local and the remote system.
		driverSettingsManagementText = _("&Allow remote system to control driver settings")
		self.driverSettingsManagementCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=driverSettingsManagementText
		))
		self.driverSettingsManagementCheckbox.Value = configuration.getDriverSettingsManagement()

		# Translators: The label for a setting in NVDA RD settings to enable
		# persistent registration of RD Pipe to the Windows registry.
		persistentRegistrationText = _("&Persist client support when exiting NVDA")
		self.persistentRegistrationCheckbox = sizer_helper.addItem(
			wx.CheckBox(
				self,
				label=persistentRegistrationText
		))
		self.persistentRegistrationCheckbox.Value = configuration.getPersistentRegistration()

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

		self.onoperatingModeChange()

	def onoperatingModeChange(self, evt: typing.Optional[wx.CommandEvent] = None):
		if evt:
			evt.Skip()
		isClient = self.operatingModeList.IsChecked(configuration.OperatingMode.CLIENT - 1)
		self.driverSettingsManagementCheckbox.Enable(isClient)
		self.persistentRegistrationCheckbox.Enable(isClient and config.isInstalledCopy())
		self.remoteDesktopSupportCheckbox.Enable(isClient)
		self.citrixSupportCheckbox.Enable(isClient and rdPipe.isCitrixSupported())
		self.recoverRemoteSpeechCheckbox.Enable(
			self.operatingModeList.IsChecked(configuration.OperatingMode.SERVER - 1)
		)

	def isValid(self):
		if not self.operatingModeList.CheckedItems:
			messageBox(
				# Translators: Message to report wrong configuration of operating mode.
				_("You need to enable NVDA RD for at least incoming or outgoing connections."),
				# Translators: The title of the message box
				_("Error"),
				wx.OK | wx.ICON_ERROR,
				self
			)
			return False
		return super().isValid()

	def onSave(self):
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.OPERATING_MODE_SETTING_NAME] = (
			functools.reduce(operator.or_, (i + 1 for i in self.operatingModeList.CheckedItems))
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.RECOVER_REMOTE_SPEECH_SETTING_NAME] = (
			self.recoverRemoteSpeechCheckbox.IsChecked()
		)
		isClient = self.operatingModeList.IsChecked(configuration.OperatingMode.CLIENT - 1)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.DRIVER_settings_MANAGEMENT_SETTING_NAME] = (
			self.driverSettingsManagementCheckbox.IsChecked()
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.PERSISTENT_REGISTRATION_SETTING_NAME] = (
			self.persistentRegistrationCheckbox.IsChecked()
			and isClient
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.REMOTE_DESKTOP_SETTING_NAME] = (
			self.remoteDesktopSupportCheckbox.IsChecked()
		)
		config.conf[configuration.CONFIG_SECTION_NAME][configuration.CITRIX_SETTING_NAME] = (
			self.citrixSupportCheckbox.IsChecked()
			and rdPipe.isCitrixSupported()
		)

		self.post_onSave.notify()
