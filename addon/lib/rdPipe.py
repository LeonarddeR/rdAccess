# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import os.path
import platform
import subprocess
import sysconfig
import tempfile
import winreg
from enum import StrEnum, unique
from functools import cached_property
from typing import Final

import addonHandler
from logHandler import log
from utils.displayString import DisplayStringIntEnum

COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE: Final[str] = "NVDA-BRAILLE"
COM_CLS_CHANNEL_NAMES_VALUE_SPEECH: Final[str] = "NVDA-SPEECH"
COM_CLASS_FOLDER: Final[str] = r"SOFTWARE\Classes\CLSID\{D1F74DC7-9FDE-45BE-9251-FA72D4064DA3}"
CTX_MODULES_FOLDER: Final[str] = r"SOFTWARE\Citrix\ICA Client\Engine\Configuration\Advanced\Modules"
CTX_RD_PIPE_FOLDER: Final[str] = os.path.join(CTX_MODULES_FOLDER, "DVCPlugin_RdPipe")
CTX_DVC_PLUGINS_FOLDER: Final[str] = os.path.join(CTX_MODULES_FOLDER, "DvcPlugins")
CTX_ARP_FOLDER: Final[str] = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CitrixOnlinePluginPackWeb"
TS_ADD_INS_FOLDER: Final[str] = r"Software\Microsoft\Terminal Server Client\Default\AddIns\RdPipe"


def isCitrixSupported() -> bool:
	try:
		with winreg.OpenKey(
			winreg.HKEY_LOCAL_MACHINE,
			CTX_ARP_FOLDER,
			0,
			winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
		):
			pass
	except OSError:
		return False
	try:
		with winreg.OpenKey(
			winreg.HKEY_CURRENT_USER,
			CTX_MODULES_FOLDER,
			0,
			winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
		):
			return True
	except OSError:
		return False


class Architecture(StrEnum):
	X86 = "x86"
	AMD64 = "AMD64"
	ARM64 = "ARM64"

	@cached_property
	def dllPath(self) -> str:
		addon = addonHandler.getCodeAddon()
		match self:
			case Architecture.AMD64:
				archPart = "x64"
			case _:
				archPart = self.lower()

		expectedPath = os.path.join(addon.path, "dll", archPart, "rd_pipe.dll")
		if not os.path.isfile(expectedPath):
			raise FileNotFoundError(expectedPath)
		return expectedPath


defaultArchitecture: Final[Architecture] = Architecture(platform.machine())
match sysconfig.get_platform():
	case "win32":
		nvdaArchitecture = Architecture.X86
	case "win-amd64":
		nvdaArchitecture = Architecture.AMD64
	case "win-arm64":
		nvdaArchitecture = Architecture.ARM64
	case _:
		raise RuntimeError(f"Unsupported platform: {_}")

SYSTEM_ROOT = os.path.expandvars("%SYSTEMROOT%")
if defaultArchitecture is Architecture.AMD64 and nvdaArchitecture is Architecture.X86:
	SYSTEM32_64 = os.path.join(
		SYSTEM_ROOT, "Sysnative"
	)  # Virtual folder for reaching 64-bit exes from 32-bit apps
else:
	SYSTEM32_64 = os.path.join(SYSTEM_ROOT, "System32")  # type: ignore

if defaultArchitecture is Architecture.AMD64:
	SYSTEM32_32 = os.path.join(SYSTEM_ROOT, "SysWOW64")
else:
	SYSTEM32_32 = SYSTEM32_64  # type: ignore


def execRegsrv(params: list[str], architecture: Architecture = defaultArchitecture):
	# Points to the 32-bit version, on Windows 32-bit or 64-bit.
	regsvr32 = os.path.join(SYSTEM32_32 if architecture is Architecture.X86 else SYSTEM32_64, "regsvr32.exe")
	# Make sure a console window doesn't show when running regsvr32.exe
	startupInfo = subprocess.STARTUPINFO()
	startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	startupInfo.wShowWindow = subprocess.SW_HIDE
	log.debug(f"Running {regsvr32!r} with params: {params}")
	subprocess.run(
		[regsvr32, *params],
		startupinfo=startupInfo,
		check=True,
		capture_output=True,
		text=True,
	)


class CommandFlags(StrEnum):
	COM_SERVER = "c"
	RDP = "r"
	CITRIX = "x"


def dllInstall(
	install: bool,
	comServer: bool,
	rdp: bool,
	citrix: bool,
	architecture: Architecture = defaultArchitecture,
):
	path = architecture.dllPath
	command = ""
	if rdp:
		command += CommandFlags.RDP
	if citrix:
		command += CommandFlags.CITRIX
	if comServer:
		command += CommandFlags.COM_SERVER
		if install:
			command += f" {COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE} {COM_CLS_CHANNEL_NAMES_VALUE_SPEECH}"
	cmdLine = ["/s", f'/i:"{command}"', "/n"]
	if not install:
		cmdLine.append("/u")
	cmdLine.append(path)
	execRegsrv(cmdLine, architecture)


@unique
class RdPipeLogLevel(DisplayStringIntEnum):
	DEFAULT = 0
	ERROR = 1
	WARN = 2
	INFO = 3
	DEBUG = 4
	TRACE = 5

	@property
	def _displayStringLabels(self):
		return {i: i._name_.title() for i in RdPipeLogLevel}


LOG_FILE_PATH = os.path.join(tempfile.gettempdir(), "rdPipe.log")


def logFileExists() -> bool:
	return os.path.isfile(LOG_FILE_PATH)


def getRdPipeLogLevel() -> RdPipeLogLevel:
	try:
		with winreg.OpenKey(
			winreg.HKEY_CURRENT_USER,
			COM_CLASS_FOLDER,
			0,
			winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
		) as key:
			value, _reg_type = winreg.QueryValueEx(key, "LogLevel")
			return RdPipeLogLevel(value)
	except OSError:
		return RdPipeLogLevel.DEFAULT


def setRdPipeLogLevel(level: RdPipeLogLevel) -> None:
	with winreg.OpenKey(
		winreg.HKEY_CURRENT_USER,
		COM_CLASS_FOLDER,
		0,
		winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY,
	) as key:
		if level == RdPipeLogLevel.DEFAULT:
			# Remove the value if it exists, ignore if not found
			try:
				winreg.DeleteValue(key, "LogLevel")
			except FileNotFoundError:
				pass
		else:
			# Set the value as the underlying int value of the enum
			winreg.SetValueEx(key, "LogLevel", 0, winreg.REG_DWORD, level.value)
