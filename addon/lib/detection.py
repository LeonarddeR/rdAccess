import bdDetect
from .sessionTrackingEx import WTSIsRemoteSession
from .protocol import DriverType
from typing import (
	List,
	Optional
)

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
	if WTSIsRemoteSession():
		port = f"NVDA-{driverType.name}"
		yield (RemoteDriver.name, bdDetect.DeviceMatch(type=KEY_VIRTUAL_CHANNEL, id=port, port=port, deviceInfo={}))
