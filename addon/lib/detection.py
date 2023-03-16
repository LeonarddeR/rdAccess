import bdDetect
from .wtsVirtualChannel import getRemoteSessionMetrics
from .protocol import DriverType
from typing import (
	List,
	Optional
)
from .namedPipe import PIPE_DIRECTORY, getSecureDesktopNamedPipes
import os.path

KEY_VIRTUAL_CHANNEL = "WTSVirtualChannel"
KEY_NAMED_PIPE_SERVER = "NamedPipeServer"
KEY_NAMED_PIPE_CLIENT = "NamedPipeClient"


def bgScanRD(
		driverType: DriverType = DriverType.BRAILLE,
		limitToDevices: Optional[List[str]] = None,
):
	from .driver import RemoteDriver
	if limitToDevices and RemoteDriver.name not in limitToDevices:
		return
	if getRemoteSessionMetrics():
		port = f"NVDA-{driverType.name}"
		yield (RemoteDriver.name, bdDetect.DeviceMatch(type=KEY_VIRTUAL_CHANNEL, id=port, port=port, deviceInfo={}))
	sdId = f"NVDA_SD-{driverType.name}"
	sdPort = os.path.join(PIPE_DIRECTORY, sdId)
	if sdPort in getSecureDesktopNamedPipes():
		yield (
			RemoteDriver.name,
			bdDetect.DeviceMatch(type=KEY_NAMED_PIPE_CLIENT, id=sdId, port=sdPort, deviceInfo={})
		)
