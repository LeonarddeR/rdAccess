# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2025 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import json
import typing
import winreg

import addonHandler
import ui
import versionInfo
import winVersion
from utils.security import isRunningOnSecureDesktop

if typing.TYPE_CHECKING:
	from ...lib import configuration, rdPipe, wtsVirtualChannel
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	configuration = addon.loadModule("lib.configuration")
	rdPipe = addon.loadModule("lib.rdPipe")
	wtsVirtualChannel = addon.loadModule("lib.wtsVirtualChannel")


def dumpRegistryKey(hive: winreg._KeyType, subkey: str) -> str | dict[str, typing.Any]:
	result = {}

	try:
		with winreg.OpenKey(hive, subkey) as key:
			i = 0
			while True:
				try:
					name, value, _ = winreg.EnumValue(key, i)
					result[name] = value
					i += 1
				except OSError:
					break

			subkeys = []
			i = 0
			while True:
				try:
					subkey_name = winreg.EnumKey(key, i)
					subkeys.append(subkey_name)
					i += 1
				except OSError:
					break

			# Recursief door de subkeys lopen en de inhoud dumpen
			for subkey_name in subkeys:
				subkey_path = f"{subkey}\\{subkey_name}"
				result[subkey_name] = dumpRegistryKey(hive, subkey_path)

	except FileNotFoundError:
		return "Not found"
	return result


def _getDiagnosticsReportDict() -> dict[str, typing.Any]:
	diagnostics = {
		"configuration": configuration.getConfigCache(ensureUpdated=True),
		"addonManifest": addon.manifest,
		"nvda": {
			"version": versionInfo.version,
		},
		"system": {
			"defaultArchitecture": rdPipe.DEFAULT_ARCHITECTURE,
			"isCitrixSupported": rdPipe.isCitrixSupported(),
			"isRunningOnSecureDesktop": isRunningOnSecureDesktop(),
			"remoteSessionMetrics": wtsVirtualChannel.getRemoteSessionMetrics(),
			"windowsVersion": str(winVersion.getWinVer()),
		},
		"registry": {
			"HKEY_CURRENT_USER": dumpRegistryKey(winreg.HKEY_CURRENT_USER, ""),
			"HKEY_LOCAL_MACHINE": dumpRegistryKey(winreg.HKEY_LOCAL_MACHINE, ""),
		},
	}
	return diagnostics


def getDiagnosticsReport() -> str:
	return json.dumps(
		_getDiagnosticsReportDict(),
		indent="\t",
	)


def showDiagnosticsReport():
	ui.browseableMessage(
		getDiagnosticsReport(),
		# Translators: Title of the diagnostics report dialog.
		title=_("RDAccess Diagnostics"),
		isHtml=False,
		closeButton=True,
		copyButton=True,
	)
