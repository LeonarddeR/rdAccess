import winreg
import os.path
from enum import Enum
import addonHandler
import platform
import shlobj
import atexit
from comtypes import GUID
from typing import Tuple

CLSID_RD_PIPE_PLUGIN = GUID("{D1F74DC7-9FDE-45BE-9251-FA72D4064DA3}")
RD_PIPE_PLUGIN_NAME = "RdPipe"
COM_CLS_FOLDER = rf"SOFTWARE\Classes\CLSID\{str(CLSID_RD_PIPE_PLUGIN)}"
COM_CLS_CHANNEL_NAMES_VALUE_NAME = "ChannelNames"
COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE = "NVDA-BRAILLE"
COM_CLS_CHANNEL_NAMES_VALUE_SPEECH = "NVDA-SPEECH"
COM_IMPROC_SERVER_FOLDER_NAME = "InprocServer32"
COM_IMPROC_SERVER_FOLDER = os.path.join(COM_CLS_FOLDER, COM_IMPROC_SERVER_FOLDER_NAME)
TS_ADD_INS_FOLDER = os.path.join("Software", "Microsoft", "Terminal Server Client", "Default", "AddIns")
TS_ADD_IN_RD_PIPE_FOLDER_NAME = RD_PIPE_PLUGIN_NAME
TS_ADD_IN_RD_PIPE_FOLDER = os.path.join(TS_ADD_INS_FOLDER, TS_ADD_IN_RD_PIPE_FOLDER_NAME)
TS_ADD_IN_NAME_VALUE_NAME = "Name"
TS_ADD_IN_VIEW_ENABLED_VALUE_NAME = "View Enabled"
CTX_MODULES_FOLDER = r"SOFTWARE\Citrix\ICA Client\Engine\Configuration\Advanced\Modules"
CTX_MODULE_RD_PIPE_FOLDER_NAME = f"DVCPlugin_{RD_PIPE_PLUGIN_NAME}"
CTX_MODULE_RD_PIPE_FOLDER = os.path.join(CTX_MODULES_FOLDER, CTX_MODULE_RD_PIPE_FOLDER_NAME)
CTX_MODULE_DVC_ADAPTER_FOLDER = os.path.join(CTX_MODULES_FOLDER, "DVCAdapter")
CTX_MODULE_DVC_ADAPTER_PLUGINS_VALUE_NAAME = "DvcPlugins"


class Architecture(str, Enum):
	X86 = "x86"
	AMD64 = "AMD64"
	ARM64 = "ARM64"


DEFAULT_ARCHITECTURE = Architecture(platform.machine())


def inprocServerKeyExists(key, architecture: Architecture = DEFAULT_ARCHITECTURE) -> bool:
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	try:
		with winreg.OpenKey(key, COM_IMPROC_SERVER_FOLDER, winreg.KEY_READ | archKey) as key:
			return True
	except FileNotFoundError:
	    return False


def getDllPath(architecture: Architecture = DEFAULT_ARCHITECTURE) -> Tuple[str, int]:
	addon = addonHandler.getCodeAddon()
	expectedPath = os.path.join(addon.path, "dll", f"rd_pipe_{architecture.lower()}.dll")
	if not os.path.isfile(expectedPath):
		raise FileNotFoundError(expectedPath)
	regType = winreg.REG_SZ
	roamingAppData = shlobj.SHGetKnownFolderPath(shlobj.FolderId.ROAMING_APP_DATA)
	localAppData = shlobj.SHGetKnownFolderPath(shlobj.FolderId.LOCAL_APP_DATA)
	if expectedPath.startswith(roamingAppData):
		expectedPath = expectedPath.replace(roamingAppData, "%appdata%")
		regType = winreg.REG_EXPAND_SZ
	elif expectedPath.startswith(localAppData):
		expectedPath = expectedPath.replace(localAppData, "%localappdata%")
		regType = winreg.REG_EXPAND_SZ
	return (expectedPath, regType)


def inprocServerAddToRegistry(
		parentKey,
		persistent: bool = False,
		architecture: Architecture = DEFAULT_ARCHITECTURE
):
	atexit.unregister(inprocServerDeleteFromRegistry)
	path, pathRegType = getDllPath(architecture)
	subKey = COM_CLS_FOLDER
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | archKey
	with winreg.CreateKeyEx(parentKey, subKey, 0, openFlags) as handle:
		winreg.SetValueEx(handle, None, 0, winreg.REG_SZ, RD_PIPE_PLUGIN_NAME)
		try:
			channels, channelsRegType = winreg.QueryValueEx(handle, COM_CLS_CHANNEL_NAMES_VALUE_NAME)
			if not isinstance(channels, list) or channelsRegType != winreg.REG_MULTI_SZ:
				raise FileNotFoundError
		except FileNotFoundError:
			channels = []
		if COM_CLS_CHANNEL_NAMES_VALUE_SPEECH not in channels:
			channels.append(COM_CLS_CHANNEL_NAMES_VALUE_SPEECH)
		if COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE not in channels:
			channels.append(COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE)
		winreg.SetValueEx(handle, COM_CLS_CHANNEL_NAMES_VALUE_NAME, 0, winreg.REG_MULTI_SZ, channels)
		with winreg.CreateKeyEx(handle, COM_IMPROC_SERVER_FOLDER_NAME, 0, openFlags) as improcHandle:
			winreg.SetValueEx(improcHandle, None, 0, pathRegType, path)
			winreg.SetValueEx(improcHandle, "ThreadingModel", 0, winreg.REG_SZ, "Free")
	if not persistent:
		atexit.register(RdsDeleteFromRegistry, parentKey)


def inprocServerDeleteFromRegistry(
		parentKey,
		undoregisterAtExit: bool = True,
		architecture: Architecture = DEFAULT_ARCHITECTURE
):
	if undoregisterAtExit:
		atexit.unregister(RdsDeleteFromRegistry)
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | archKey
	winreg.DeleteKeyEx(parentKey, COM_IMPROC_SERVER_FOLDER, openFlags)
	winreg.DeleteKeyEx(parentKey, COM_CLS_FOLDER, openFlags)


def RdsKeyExists(key, architecture: Architecture = DEFAULT_ARCHITECTURE) -> bool:
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	try:
		with winreg.OpenKey(key, TS_ADD_IN_RD_PIPE_FOLDER, winreg.KEY_READ | archKey) as key:
			return True
	except FileNotFoundError:
	    return False


def RdsAddToRegistry(
		parentKey,
		persistent: bool = False,
		architecture: Architecture = DEFAULT_ARCHITECTURE
):
	atexit.unregister(RdsDeleteFromRegistry)
	subKey = TS_ADD_IN_RD_PIPE_FOLDER
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | archKey
	with winreg.CreateKeyEx(parentKey, subKey, 0, openFlags) as handle:
		winreg.SetValueEx(handle, TS_ADD_IN_NAME_VALUE_NAME, 0, winreg.REG_SZ, str(CLSID_RD_PIPE_PLUGIN))
		winreg.SetValueEx(handle, TS_ADD_IN_VIEW_ENABLED_VALUE_NAME, 0, winreg.REG_DWORD, int(True))
	if not persistent:
		atexit.register(RdsDeleteFromRegistry, parentKey)


def RdsDeleteFromRegistry(
		parentKey,
		undoregisterAtExit: bool = True,
		architecture: Architecture = DEFAULT_ARCHITECTURE
):
	if undoregisterAtExit:
		atexit.unregister(RdsDeleteFromRegistry)
	archKey = winreg.KEY_WOW64_32KEY if architecture == Architecture.X86 else winreg.KEY_WOW64_64KEY
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | archKey
	winreg.DeleteKeyEx(parentKey, TS_ADD_IN_RD_PIPE_FOLDER, openFlags)


def CitrixAddToRegistry(parentKey):
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY
	with winreg.CreateKeyEx(parentKey, CTX_MODULE_RD_PIPE_FOLDER_NAME, 0, openFlags) as handle:
		winreg.SetValueEx(handle, "DvcNames", 0, winreg.REG_SZ, RD_PIPE_PLUGIN_NAME)
		winreg.SetValueEx(handle, "PluginClassId", 0, winreg.REG_SZ, str(CLSID_RD_PIPE_PLUGIN))
	with winreg.OpenKeyEx(parentKey, CTX_MODULE_DVC_ADAPTER_FOLDER, 0, openFlags) as handle:
		plugins, regType = winreg.QueryValueEx(handle, CTX_MODULE_DVC_ADAPTER_PLUGINS_VALUE_NAAME)
		pluginsList = plugins.split(",")
		if RD_PIPE_PLUGIN_NAME not in pluginsList:
			pluginsList.append(RD_PIPE_PLUGIN_NAME)
			winreg.SetValueEx(handle, CTX_MODULE_DVC_ADAPTER_PLUGINS_VALUE_NAAME, 0, regType, ",".join(pluginsList))


def CitrixDeleteFromRegistry(parentKey):
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY
	winreg.DeleteKeyEx(parentKey, CTX_MODULE_RD_PIPE_FOLDER, openFlags)
	with winreg.OpenKeyEx(parentKey, CTX_MODULE_DVC_ADAPTER_FOLDER, 0, openFlags) as handle:
		plugins, regType = winreg.QueryValueEx(handle, CTX_MODULE_DVC_ADAPTER_PLUGINS_VALUE_NAAME)
		pluginsList = plugins.split(",")
		if RD_PIPE_PLUGIN_NAME in pluginsList:
			pluginsList.remove(RD_PIPE_PLUGIN_NAME)
			winreg.SetValueEx(handle, CTX_MODULE_DVC_ADAPTER_PLUGINS_VALUE_NAAME, 0, regType, ",".join(pluginsList))
