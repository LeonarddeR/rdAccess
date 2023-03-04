import os.path
from enum import Enum
import addonHandler
import platform
import COMRegistrationFixes
import subprocess
import shellapi
import winUser
import winKernel
from ctypes import windll, byref
from ctypes.wintypes import HANDLE, MSG
from typing import Optional
from logHandler import log

COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE = "NVDA-BRAILLE"
COM_CLS_CHANNEL_NAMES_VALUE_SPEECH = "NVDA-SPEECH"
CTX_MODULES_FOLDER = r"SOFTWARE\Citrix\ICA Client\Engine\Configuration\Advanced\Modules"
CTX_RD_PIPE_FOLDER = os.path.join(CTX_MODULES_FOLDER, "DVCPlugin_RdPipe")
CTX_ARP_FOLDER = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CitrixOnlinePluginPackWeb"


def isCitrixWorkspaceInstalled() -> bool:
	import winreg
	try:
		with winreg.OpenKey(
			winreg.HKEY_LOCAL_MACHINE,
			CTX_ARP_FOLDER,
			0,
			winreg.KEY_READ | winreg.KEY_WOW64_32KEY
		):
			return True
	except OSError:
		return False


def isCitrixSupportRegistered() -> bool:
	import winreg
	try:
		with winreg.OpenKey(
			winreg.HKEY_LOCAL_MACHINE,
			CTX_RD_PIPE_FOLDER,
			0,
			winreg.KEY_READ | winreg.KEY_WOW64_32KEY
		):
			return True
	except OSError:
		return False


class Architecture(str, Enum):
	X86 = "x86"
	AMD64 = "AMD64"
	ARM64 = "ARM64"


DEFAULT_ARCHITECTURE = Architecture(platform.machine())


def execRegsrv(
		params: str,
		architecture: Architecture = DEFAULT_ARCHITECTURE,
		elevated: bool = False
	# Adapted from systemUtils.execElevated
) -> Optional[int]:
	if architecture is Architecture.X86:
		# Points to the 32-bit version, on Windows 32-bit or 64-bit.
		regsvr32 = os.path.join(COMRegistrationFixes.SYSTEM32, "regsvr32.exe")
	else:
		# SysWOW64 provides a virtual directory to allow 32-bit programs to reach 64-bit executables.
		regsvr32 = os.path.join(COMRegistrationFixes.SYSNATIVE, "regsvr32.exe")
	import wx
	wait = wx.GetApp() is not None
	# Make sure a console window doesn't show when running regsvr32.exe
	sei = shellapi.SHELLEXECUTEINFO(lpFile=regsvr32, lpParameters=params, nShow=winUser.SW_HIDE)
	if elevated:
		sei.lpVerb = "runas"
	if wait:
		sei.fMask = shellapi.SEE_MASK_NOCLOSEPROCESS
	shellapi.ShellExecuteEx(sei)
	if not wait:
		return
	try:
		h = HANDLE(sei.hProcess)
		msg = MSG()
		while windll.user32.MsgWaitForMultipleObjects(1, byref(h), False, -1, 255) == 1:
			while windll.user32.PeekMessageW(byref(msg), None, 0, 0, 1):
				windll.user32.TranslateMessage(byref(msg))
				windll.user32.DispatchMessageW(byref(msg))
		exitCode = winKernel.GetExitCodeProcess(sei.hProcess)
		if exitCode != 0:
			log.error(f"Executing {regsvr32!r} with params {params!r} failed with exit code {exitCode}")
		return exitCode
	finally:
		winKernel.closeHandle(sei.hProcess)


class CommandFlags(str, Enum):
	COM_SERVER = "c"
	RDP = "r"
	CITRIX = "x"
	LOCAL_MACHINE = "m"


def getDllPath(architecture: Architecture = DEFAULT_ARCHITECTURE) -> str:
	addon = addonHandler.getCodeAddon()
	expectedPath = os.path.join(addon.path, "dll", f"rd_pipe_{architecture.lower()}.dll")
	if not os.path.isfile(expectedPath):
		raise FileNotFoundError(expectedPath)
	return expectedPath


def dllInstall(
		install: bool,
		comServer: bool,
		rdp: bool,
		citrix: bool,
		localMachine: bool = False,
		architecture: Architecture = DEFAULT_ARCHITECTURE,
) -> bool:
	path = getDllPath(architecture)
	command = ""
	if localMachine:
		command += CommandFlags.LOCAL_MACHINE
	if rdp:
		command += CommandFlags.RDP
	if citrix:
		command += CommandFlags.CITRIX
	if comServer:
		command += CommandFlags.COM_SERVER
		if install:
			command += f" {COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE} {COM_CLS_CHANNEL_NAMES_VALUE_SPEECH}"
	cmdLine = ["/s", f"/i:\"{command}\"", "/n"]
	if not install:
		cmdLine.append("/u")
	cmdLine.append(path)
	res = execRegsrv(subprocess.list2cmdline(cmdLine), architecture, localMachine)
	return not bool(res)
