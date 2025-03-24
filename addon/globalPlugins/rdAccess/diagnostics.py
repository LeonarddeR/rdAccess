# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2025 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import json
import typing

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
	}
	return diagnostics


def getDiagnosticsReport() -> str:
	return json.dumps(_getDiagnosticsReportDict(), indent='\t',)


def showDiagnosticsReport():
	ui.browseableMessage(
		getDiagnosticsReport(),
		# Translators: Title of the diagnostics report dialog.
		title=_("RDAccess Diagnostics"),
		isHtml=False,
		closeButton=True,
		copyButton=True,
	)
