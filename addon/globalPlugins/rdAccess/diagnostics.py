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
import wx
from utils.security import isRunningOnSecureDesktop

addon: addonHandler.Addon = addonHandler.getCodeAddon()
if typing.TYPE_CHECKING:
	from ...lib import (
		configuration,
		namedPipe,
		rdPipe,
		wtsVirtualChannel,
	)
else:
	configuration = addon.loadModule("lib.configuration")
	namedPipe = addon.loadModule("lib.namedPipe")
	rdPipe = addon.loadModule("lib.rdPipe")
	wtsVirtualChannel = addon.loadModule("lib.wtsVirtualChannel")

_supportsBrowseableMessageButtons = versionInfo.version_year >= 2025


def dumpRegistryKey(
	hive,
	subkey: str,
	x86: bool = False,
) -> str | dict[str, typing.Any]:
	result = {}

	try:
		with winreg.OpenKey(
			hive,
			subkey,
			access=winreg.KEY_READ | (winreg.KEY_WOW64_32KEY if x86 else winreg.KEY_WOW64_64KEY),
		) as key:
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

	except Exception as e:
		return str(e)
	return result


def _getDiagnosticsReportDict() -> dict[str, typing.Any]:
	diagnostics = {
		"configuration": configuration.getConfigCache(ensureUpdated=True),
		"addonManifest": addon.manifest,
		"nvda": {
			"version": versionInfo.version,
		},
		"rdPipe": {
			"availablePipes": list(namedPipe.getRdPipeNamedPipes()),
		},
		"system": {
			"defaultArchitecture": rdPipe.defaultArchitecture,
			"nvdaArchitecture": rdPipe.nvdaArchitecture,
			"isCitrixSupported": rdPipe.isCitrixSupported(),
			"isRunningOnSecureDesktop": isRunningOnSecureDesktop(),
			"remoteSessionMetrics": wtsVirtualChannel.getRemoteSessionMetrics(),
			"windowsVersion": str(winVersion.getWinVer()),
		},
		"registry": {
			"currentUser": {
				rdPipe.COM_CLASS_FOLDER: dumpRegistryKey(winreg.HKEY_CURRENT_USER, rdPipe.COM_CLASS_FOLDER),
				rdPipe.TS_ADD_INS_FOLDER: dumpRegistryKey(winreg.HKEY_CURRENT_USER, rdPipe.TS_ADD_INS_FOLDER),
				rdPipe.CTX_RD_PIPE_FOLDER: dumpRegistryKey(
					winreg.HKEY_CURRENT_USER,
					rdPipe.CTX_RD_PIPE_FOLDER,
				),
				rdPipe.CTX_DVC_PLUGINS_FOLDER: dumpRegistryKey(
					winreg.HKEY_CURRENT_USER,
					rdPipe.CTX_DVC_PLUGINS_FOLDER,
				),
			},
			"localMachine": {
				rdPipe.COM_CLASS_FOLDER: dumpRegistryKey(winreg.HKEY_LOCAL_MACHINE, rdPipe.COM_CLASS_FOLDER),
				rdPipe.TS_ADD_INS_FOLDER: dumpRegistryKey(
					winreg.HKEY_LOCAL_MACHINE,
					rdPipe.TS_ADD_INS_FOLDER,
				),
			},
		},
	}
	return diagnostics


def getDiagnosticsReport() -> str:
	return json.dumps(
		_getDiagnosticsReportDict(),
		indent="\t",
	)


def showDiagnosticsReport(_evt: wx.CommandEvent | None = None):
	kwargs = {
		"message": getDiagnosticsReport(),
		# Translators: Title of the diagnostics report dialog.
		"title": _("RDAccess Diagnostics"),
	}
	if _supportsBrowseableMessageButtons:
		kwargs.update(
			closeButton=True,
			copyButton=True,
		)
	ui.browseableMessage(**kwargs)
