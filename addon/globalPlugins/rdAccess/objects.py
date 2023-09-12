# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

from NVDAObjects import NVDAObject
from NVDAObjects.IAccessible import IAccessible


class RemoteDesktopControl(NVDAObject):
    ...


class OutOfProcessChannelRemoteDesktopControl(RemoteDesktopControl):
    ...


def findExtraOverlayClasses(obj, clsList):
    if not isinstance(obj, IAccessible):
        return
    elif (obj.windowClassName == "IHWindowClass" and obj.appModule.appName == "mstsc") or (
        obj.windowClassName in ("CtxICADisp", "Transparent Windows Client")
        and obj.appModule.appName == "wfica32"
    ):
        clsList.append(RemoteDesktopControl)
    elif (
        obj.windowClassName == "VMware.Horizon.Client.Sdk:RemoteWindow Class"
        and obj.appModule.appName == "vmware-view"
    ):
        clsList.append(OutOfProcessChannelRemoteDesktopControl)
