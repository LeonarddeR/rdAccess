# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import bdDetect
from utils.security import isRunningOnSecureDesktop

from . import configuration
from .protocol import DriverType
from .wtsVirtualChannel import getRemoteSessionMetrics


def bgScanRD(
	driverType: DriverType = DriverType.BRAILLE,
	limitToDevices: list[str] | None = None,
):
	from .driver import RemoteDriver

	operatingMode = configuration.getOperatingMode()
	if limitToDevices and RemoteDriver.name not in limitToDevices:
		return
	isSecureDesktop: bool = isRunningOnSecureDesktop()
	if (
		operatingMode & configuration.OperatingMode.SERVER
		and not isSecureDesktop
		and getRemoteSessionMetrics() == 1
	):
		port = f"NVDA-{driverType.name}"
		yield (
			RemoteDriver.name,
			bdDetect.DeviceMatch(type=bdDetect.ProtocolType.CUSTOM, id=port, port=port, deviceInfo={}),
		)
