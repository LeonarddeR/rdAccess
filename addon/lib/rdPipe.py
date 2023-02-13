import winreg
import os.path
from enum import IntFlag, auto
import addonHandler
import platform
import shlobj
import atexit

TS_ADD_INS_FOLDER = os.path.join("Software", "Microsoft", "Terminal Server Client", "Default", "AddIns")
RD_PIPE_FOLDER_NAME = "RdPipe"
RD_PIPE_FOLDER = os.path.join(TS_ADD_INS_FOLDER, RD_PIPE_FOLDER_NAME)
NAME_VALUE_NAME = "Name"
CHANNEL_NAMES_VALUE_NAME = "ChannelNames"
CHANNEL_NAMES_VALUE_BRAILLE = "NVDA-BRAILLE"
CHANNEL_NAMES_VALUE_SPEECH = "NVDA-SPEECH"


class KeyComponents(IntFlag):
	RD_PIPE_KEY = auto()
	NAME_VALUE = auto()
	CHANNEL_NAMES_VALUE_BRAILLE = auto()
	CHANNEL_NAMES_VALUE_SPEECH = auto()
	CHANNEL_NAMES_VALUE_UNKNOWN = auto()


def keyExists(key) -> bool:
	try:
		with winreg.OpenKey(key, RD_PIPE_FOLDER, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
			return True
	except FileNotFoundError:
	    return False


def getDllPath() -> str:
	addon = addonHandler.getCodeAddon()
	expectedPath = os.path.join(addon.path, "dll", f"rd_pipe_{platform.machine().lower()}.dll")

	if not os.path.isfile(expectedPath):
		raise FileNotFoundError(expectedPath)
	roamingAppData = shlobj.SHGetKnownFolderPath(shlobj.FolderId.ROAMING_APP_DATA)
	localAppData = shlobj.SHGetKnownFolderPath(shlobj.FolderId.LOCAL_APP_DATA)
	if expectedPath.startswith(roamingAppData):
		expectedPath = expectedPath.replace(roamingAppData, "%appdata%")
	elif expectedPath.startswith(localAppData):
		expectedPath = expectedPath.replace(localAppData, "%localappdata%")
	return expectedPath


def addToRegistry(
		key,
		persistent: bool = False,
		channelNamesOnly: bool = False
) -> KeyComponents:
	atexit.unregister(deleteFromRegistry)
	expectedPath = getDllPath()
	res = KeyComponents(0)
	subKey = RD_PIPE_FOLDER
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
	needsSetValueForChannels = False
	try:
		handle = winreg.OpenKeyEx(key, subKey, 0, openFlags)
	except FileNotFoundError:
		handle = winreg.CreateKeyEx(key, subKey, 0, openFlags)
		res |= KeyComponents.RD_PIPE_KEY
	if not channelNamesOnly:
		try:
			path, regType = winreg.QueryValueEx(handle, NAME_VALUE_NAME)
			if regType == winreg.REG_EXPAND_SZ:
				path = winreg.ExpandEnvironmentStrings(path)
			if (
				path != winreg.ExpandEnvironmentStrings(expectedPath)
				and not os.path.isfile(path)
			):
				raise FileNotFoundError
		except FileNotFoundError:
			path = None
		if path is None:
			winreg.SetValueEx(
				handle,
				NAME_VALUE_NAME,
				0,
				winreg.REG_EXPAND_SZ if 'appdata%' in expectedPath else winreg.REG_SZ,
				expectedPath
			)
			res |= KeyComponents.NAME_VALUE
	try:
		channels, regType = winreg.QueryValueEx(handle, CHANNEL_NAMES_VALUE_NAME)
		if not isinstance(channels, list) or regType != winreg.REG_MULTI_SZ:
			raise FileNotFoundError
	except FileNotFoundError:
		channels = []
		needsSetValueForChannels = True
	if CHANNEL_NAMES_VALUE_SPEECH not in channels:
		channels.append(CHANNEL_NAMES_VALUE_SPEECH)
		res |= KeyComponents.CHANNEL_NAMES_VALUE_SPEECH
		needsSetValueForChannels = True
	if CHANNEL_NAMES_VALUE_BRAILLE not in channels:
		channels.append(CHANNEL_NAMES_VALUE_BRAILLE)
		res |= KeyComponents.CHANNEL_NAMES_VALUE_BRAILLE
		needsSetValueForChannels = True
	if len(channels) > 2:
		res |= KeyComponents.CHANNEL_NAMES_VALUE_UNKNOWN
	if needsSetValueForChannels:
		winreg.SetValueEx(handle, CHANNEL_NAMES_VALUE_NAME, 0, winreg.REG_MULTI_SZ, channels)
	if not persistent:
		atexit.register(deleteFromRegistry, key, res)
	return res


def deleteFromRegistry(key, components: KeyComponents, undoregisterAtExit: bool = True):
	if undoregisterAtExit:
		atexit.unregister(deleteFromRegistry)
	openFlags = winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
	if (
		KeyComponents.RD_PIPE_KEY & components
		or KeyComponents.NAME_VALUE & components
	):
		winreg.DeleteKeyEx(key, RD_PIPE_FOLDER, openFlags)
		return
	if (
		KeyComponents.CHANNEL_NAMES_VALUE_SPEECH & components
		or KeyComponents.CHANNEL_NAMES_VALUE_BRAILLE & components
	):
		handle = winreg.OpenKeyEx(key, RD_PIPE_FOLDER, 0, openFlags)
		channels, regType = winreg.QueryValueEx(handle, CHANNEL_NAMES_VALUE_NAME)
		if KeyComponents.CHANNEL_NAMES_VALUE_SPEECH & components and CHANNEL_NAMES_VALUE_SPEECH in channels:
			channels.remove(CHANNEL_NAMES_VALUE_SPEECH)
		if KeyComponents.CHANNEL_NAMES_VALUE_BRAILLE & components and CHANNEL_NAMES_VALUE_BRAILLE in channels:
			channels.remove(CHANNEL_NAMES_VALUE_BRAILLE)
		winreg.SetValueEx(handle, CHANNEL_NAMES_VALUE_NAME, 0, winreg.REG_MULTI_SZ, channels)
