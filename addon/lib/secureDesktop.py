# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import versionInfo
from extensionPoints import Action

hasSecureDesktopExtensionPoint = versionInfo.version_year >= 2024

if hasSecureDesktopExtensionPoint:
	from winAPI.secureDesktop import post_secureDesktopStateChange
else:
	post_secureDesktopStateChange = Action()
