# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from enum import unique
from typing import Any

import addonHandler
import config
from utils.displayString import DisplayStringIntFlag

addonHandler.initTranslation()
ConfigT = dict[str, Any]
_cachedConfig: ConfigT = {}


@unique
class OperatingMode(DisplayStringIntFlag):
	SERVER = 0x1
	CLIENT = 0x2
	SECURE_DESKTOP = 0x4

	@property
	def _displayStringLabels(self):
		return {
			OperatingMode.SERVER: _("Incoming connections (Remote Desktop Server)"),
			OperatingMode.CLIENT: _("Outgoing connections (Remote Desktop Client)"),
			OperatingMode.SECURE_DESKTOP: _("Secure Desktop pass through"),
		}


CONFIG_SECTION_NAME = addonHandler.getCodeAddon().name
OPERATING_MODE_SETTING_NAME = "operatingMode"
PERSISTENT_REGISTRATION_SETTING_NAME = "persistentRegistration"
REMOTE_DESKTOP_SETTING_NAME = "enableRemoteDesktopSupport"
CITRIX_SETTING_NAME = "enableCitrixSupport"
RECOVER_REMOTE_SPEECH_SETTING_NAME = "recoverRemoteSpeech"
DRIVER_settings_MANAGEMENT_SETTING_NAME = "driverSettingsManagement"
CONFIG_SPEC = {
	OPERATING_MODE_SETTING_NAME: "integer(default=3, min=1, max=7)",
	PERSISTENT_REGISTRATION_SETTING_NAME: "boolean(default=false)",
	REMOTE_DESKTOP_SETTING_NAME: "boolean(default=true)",
	CITRIX_SETTING_NAME: "boolean(default=true)",
	RECOVER_REMOTE_SPEECH_SETTING_NAME: "boolean(default=true)",
	DRIVER_settings_MANAGEMENT_SETTING_NAME: "boolean(default=false)",
}


def _getSetting(setting: str, fromCache: bool) -> Any:
	if not initialized:
		initializeConfig()
	section = _cachedConfig if fromCache else config.conf[CONFIG_SECTION_NAME]
	return section[setting]


def getOperatingMode(fromCache: bool = False) -> OperatingMode:
	return OperatingMode(int(_getSetting(OPERATING_MODE_SETTING_NAME, fromCache)))


def getPersistentRegistration(fromCache: bool = False) -> bool:
	return _getSetting(PERSISTENT_REGISTRATION_SETTING_NAME, fromCache)


def getRemoteDesktopSupport(fromCache: bool = False) -> bool:
	return _getSetting(REMOTE_DESKTOP_SETTING_NAME, fromCache)


def getCitrixSupport(fromCache: bool = False) -> bool:
	return _getSetting(CITRIX_SETTING_NAME, fromCache)


def getRecoverRemoteSpeech(fromCache: bool = False) -> bool:
	return _getSetting(RECOVER_REMOTE_SPEECH_SETTING_NAME, fromCache)


def getDriverSettingsManagement(fromCache: bool = False) -> bool:
	return _getSetting(DRIVER_settings_MANAGEMENT_SETTING_NAME, fromCache)


initialized: bool = False


def initializeConfig():
	global initialized
	if initialized:
		return
	if CONFIG_SECTION_NAME not in config.conf:
		config.conf[CONFIG_SECTION_NAME] = {}
	config.conf[CONFIG_SECTION_NAME].spec.update(CONFIG_SPEC)
	cached = updateConfigCache()
	initialized = True


def updateConfigCache():
	global _cachedConfig
	_cachedConfig = config.conf[CONFIG_SECTION_NAME].copy()


def getConfigCache(ensureUpdated: bool = True) -> ConfigT:
	if ensureUpdated:
		updateConfigCache()
	return _cachedConfig
