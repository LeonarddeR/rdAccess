# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os.path
from enum import StrEnum

import bdDetect
from utils.security import isRunningOnSecureDesktop

from . import configuration
from .namedPipe import PIPE_DIRECTORY, getSecureDesktopNamedPipes
from .protocol import DriverType
from .wtsVirtualChannel import getRemoteSessionMetrics


class BackendType(StrEnum):
	VIRTUAL_CHANNEL = "WTSVirtualChannel"
	NAMED_PIPE_CLIENT = "NamedPipeClient"


def bgScanRD(
	driverType: DriverType = DriverType.BRAILLE,
	limitToDevices: list[str] | None = None,
):
	from .driver import RemoteDriver

	operatingMode = configuration.getOperatingMode()
	if limitToDevices and RemoteDriver.name not in limitToDevices:
		return
	isSecureDesktop: bool = isRunningOnSecureDesktop()
	if isSecureDesktop and operatingMode & configuration.OperatingMode.SECURE_DESKTOP:
		sdId = f"NVDA_SD-{driverType.name}"
		sdPort = os.path.join(PIPE_DIRECTORY, sdId)
		if sdPort in getSecureDesktopNamedPipes():
			yield (
				RemoteDriver.name,
				bdDetect.DeviceMatch(type=BackendType.NAMED_PIPE_CLIENT, id=sdId, port=sdPort, deviceInfo={}),
			)
	if (
		operatingMode & configuration.OperatingMode.SERVER
		and not isSecureDesktop
		and getRemoteSessionMetrics() == 1
	):
		port = f"NVDA-{driverType.name}"
		yield (
			RemoteDriver.name,
			bdDetect.DeviceMatch(type=BackendType.VIRTUAL_CHANNEL, id=port, port=port, deviceInfo={}),
		)
