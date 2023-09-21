# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import functools
import operator
import typing

import addonHandler
import config
import wx
from extensionPoints import Action
from gui import guiHelper, messageBox, nvdaControls
from gui.settingsDialogs import SettingsPanel

if typing.TYPE_CHECKING:
    from ...lib import configuration, rdPipe
else:
    addon: addonHandler.Addon = addonHandler.getCodeAddon()
    configuration = addon.loadModule("lib.configuration")
    rdPipe = addon.loadModule("lib.rdPipe")

addonHandler.initTranslation()


class RemoteDesktopSettingsPanel(SettingsPanel):
    # Translators: The label for the NVDA Remote Desktop settings panel.
    title = _("Remote Desktop Accessibility")
    post_onSave = Action()

    def makeSettings(self, settingsSizer):
        sizer_helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        # Translators: The label for a list of check boxes in RDAccess settings to set operating mode.
        operatingModeText = _("&Enable remote desktop accessibility for")
        operatingModeChoices = [i.displayString for i in configuration.OperatingMode]
        self.operatingModes = list(configuration.OperatingMode)
        self.operatingModeList = sizer_helper.addLabeledControl(
            operatingModeText,
            nvdaControls.CustomCheckListBox,
            choices=operatingModeChoices,
        )
        self.operatingModeList.CheckedItems = [
            n for n, e in enumerate(configuration.OperatingMode) if configuration.getOperatingMode() & e
        ]
        self.operatingModeList.Select(0)
        self.operatingModeList.Bind(wx.EVT_CHECKLISTBOX, self.onoperatingModeChange)

        # Translators: This is the label for a group of options in the
        # Remote Desktop settings panel.
        serverGroupText = _("Server")
        serverGroupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=serverGroupText)
        serverGroupBox = serverGroupSizer.GetStaticBox()
        serverGroup = guiHelper.BoxSizerHelper(self, sizer=serverGroupSizer)
        sizer_helper.addItem(serverGroup)

        # Translators: The label for a setting in RDAccess settings to enable
        # automatic recovery of remote speech when the connection was lost.
        recoverRemoteSpeechText = _("&Automatically recover remote speech after connection loss")
        self.recoverRemoteSpeechCheckbox = serverGroup.addItem(
            wx.CheckBox(serverGroupBox, label=recoverRemoteSpeechText)
        )
        self.recoverRemoteSpeechCheckbox.Value = configuration.getRecoverRemoteSpeech()

        # Translators: This is the label for a group of options in the
        # Remote Desktop settings panel.
        clientGroupText = _("Client")
        clientGroupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=clientGroupText)
        clientGroupBox = clientGroupSizer.GetStaticBox()
        clientGroup = guiHelper.BoxSizerHelper(self, sizer=clientGroupSizer)
        sizer_helper.addItem(clientGroup)

        # Translators: The label for a setting in RDAccess settings to enable
        # support for exchanging driver settings between the local and the remote system.
        driverSettingsManagementText = _("&Allow remote system to control driver settings")
        self.driverSettingsManagementCheckbox = clientGroup.addItem(
            wx.CheckBox(clientGroupBox, label=driverSettingsManagementText)
        )
        self.driverSettingsManagementCheckbox.Value = configuration.getDriverSettingsManagement()

        # Translators: The label for a setting in RDAccess settings to enable
        # persistent registration of RD Pipe to the Windows registry.
        persistentRegistrationText = _("&Persist client support when exiting NVDA")
        self.persistentRegistrationCheckbox = clientGroup.addItem(
            wx.CheckBox(clientGroupBox, label=persistentRegistrationText)
        )
        self.persistentRegistrationCheckbox.Value = configuration.getPersistentRegistration()

        # Translators: The label for a setting in RDAccess settings to enable
        # registration of RD Pipe to the Windows registry for remote desktop support.
        remoteDesktopSupportText = _("Enable Microsoft &Remote Desktop support")
        self.remoteDesktopSupportCheckbox = clientGroup.addItem(
            wx.CheckBox(clientGroupBox, label=remoteDesktopSupportText)
        )
        self.remoteDesktopSupportCheckbox.Value = configuration.getRemoteDesktopSupport()

        # Translators: The label for a setting in RDAccess settings to enable
        # registration of RD Pipe to the Windows registry for Citrix support.
        citrixSupportText = _("Enable &Citrix Workspace support")
        self.citrixSupportCheckbox = clientGroup.addItem(wx.CheckBox(clientGroupBox, label=citrixSupportText))
        self.citrixSupportCheckbox.Value = configuration.getCitrixSupport()

        self.onoperatingModeChange()

    def onoperatingModeChange(self, evt: typing.Optional[wx.CommandEvent] = None):
        if evt:
            evt.Skip()
        isClient = self.operatingModeList.IsChecked(
            self.operatingModes.index(configuration.OperatingMode.CLIENT)
        )
        self.driverSettingsManagementCheckbox.Enable(isClient)
        self.persistentRegistrationCheckbox.Enable(isClient and config.isInstalledCopy())
        self.remoteDesktopSupportCheckbox.Enable(isClient)
        self.citrixSupportCheckbox.Enable(isClient and rdPipe.isCitrixSupported())
        self.recoverRemoteSpeechCheckbox.Enable(
            self.operatingModeList.IsChecked(self.operatingModes.index(configuration.OperatingMode.SERVER))
        )

    def isValid(self):
        if not self.operatingModeList.CheckedItems:
            messageBox(
                # Translators: Message to report wrong configuration of operating mode.
                _(
                    "You need to enable remote destkop accessibility support for at least "
                    "incoming or outgoing connections."
                ),
                # Translators: The title of the message box
                _("Error"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return False
        return super().isValid()

    def onSave(self):
        config.conf[configuration.CONFIG_SECTION_NAME][configuration.OPERATING_MODE_SETTING_NAME] = int(
            functools.reduce(
                operator.or_,
                (self.operatingModes[i] for i in self.operatingModeList.CheckedItems),
            )
        )
        config.conf[configuration.CONFIG_SECTION_NAME][
            configuration.RECOVER_REMOTE_SPEECH_SETTING_NAME
        ] = self.recoverRemoteSpeechCheckbox.IsChecked()
        isClient = self.operatingModeList.IsChecked(
            self.operatingModes.index(configuration.OperatingMode.CLIENT)
        )
        config.conf[configuration.CONFIG_SECTION_NAME][
            configuration.DRIVER_settings_MANAGEMENT_SETTING_NAME
        ] = self.driverSettingsManagementCheckbox.IsChecked()
        config.conf[configuration.CONFIG_SECTION_NAME][configuration.PERSISTENT_REGISTRATION_SETTING_NAME] = (
            self.persistentRegistrationCheckbox.IsChecked() and isClient
        )
        config.conf[configuration.CONFIG_SECTION_NAME][
            configuration.REMOTE_DESKTOP_SETTING_NAME
        ] = self.remoteDesktopSupportCheckbox.IsChecked()
        config.conf[configuration.CONFIG_SECTION_NAME][configuration.CITRIX_SETTING_NAME] = (
            self.citrixSupportCheckbox.IsChecked() and rdPipe.isCitrixSupported()
        )

        self.post_onSave.notify()
