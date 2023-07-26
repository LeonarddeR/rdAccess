# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import bdDetect
from .wtsVirtualChannel import getRemoteSessionMetrics
from .protocol import DriverType
from . import configuration
from typing import (
	List,
	Optional
)
from .namedPipe import PIPE_DIRECTORY, getSecureDesktopNamedPipes
import os.path
from utils.security import isRunningOnSecureDesktop

KEY_VIRTUAL_CHANNEL = "WTSVirtualChannel"
KEY_NAMED_PIPE_SERVER = "NamedPipeServer"
KEY_NAMED_PIPE_CLIENT = "NamedPipeClient"


def bgScanRD(
		driverType: DriverType = DriverType.BRAILLE,
		limitToDevices: Optional[List[str]] = None,
):
	from .driver import RemoteDriver
	operatingMode = configuration.getOperatingMode()
	if limitToDevices and RemoteDriver.name not in limitToDevices:
		return
	if isRunningOnSecureDesktop() and operatingMode & configuration.OperatingMode.SECURE_DESKTOP:
		sdId = f"NVDA_SD-{driverType.name}"
		sdPort = os.path.join(PIPE_DIRECTORY, sdId)
		if sdPort in getSecureDesktopNamedPipes():
			yield (
				RemoteDriver.name,
				bdDetect.DeviceMatch(type=KEY_NAMED_PIPE_CLIENT, id=sdId, port=sdPort, deviceInfo={})
			)
	if operatingMode & configuration.OperatingMode.SERVER and getRemoteSessionMetrics() == 1:
		port = f"NVDA-{driverType.name}"
		yield (RemoteDriver.name, bdDetect.DeviceMatch(type=KEY_VIRTUAL_CHANNEL, id=port, port=port, deviceInfo={}))


def register():
	bdDetect.scanForDevices.register(bgScanRD)
	bdDetect.scanForDevices.moveToEnd(bgScanRD, last=False)


def unregister():
	bdDetect.scanForDevices.unregister(bgScanRD)
