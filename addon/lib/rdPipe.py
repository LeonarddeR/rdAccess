import os.path
from enum import Enum
import addonHandler
import platform
import atexit
import COMRegistrationFixes
import subprocess
import shellapi
import winUser
import winKernel
from ctypes import windll, byref
from ctypes.wintypes import HANDLE, MSG
from logHandler import log

COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE = "NVDA-BRAILLE"
COM_CLS_CHANNEL_NAMES_VALUE_SPEECH = "NVDA-SPEECH"


class Architecture(str, Enum):
	X86 = "x86"
	AMD64 = "AMD64"
	ARM64 = "ARM64"


DEFAULT_ARCHITECTURE = Architecture(platform.machine())


def execRegsrv(
		params: str,
		architecture: Architecture = DEFAULT_ARCHITECTURE,
		elevated: bool = False
):
	if architecture is Architecture.X86:
		# Points to the 32-bit version, on Windows 32-bit or 64-bit.
		regsvr32 = os.path.join(COMRegistrationFixes.SYSTEM32, "regsvr32.exe")
	else:
		# SysWOW64 provides a virtual directory to allow 32-bit programs to reach 64-bit executables.
		regsvr32 = os.path.join(COMRegistrationFixes.SYSNATIVE, "regsvr32.exe")
	# Make sure a console window doesn't show when running regsvr32.exe
	sei = shellapi.SHELLEXECUTEINFO(lpFile=regsvr32, lpParameters=params, nShow=winUser.SW_HIDE)
	if elevated:
		sei.lpVerb = "runas"
	sei.fMask = shellapi.SEE_MASK_NOCLOSEPROCESS
	shellapi.ShellExecuteEx(sei)
	try:
		h = HANDLE(sei.hProcess)
		msg = MSG()
		while windll.user32.MsgWaitForMultipleObjects(1, byref(h), False, -1, 255) == 1:
			while windll.user32.PeekMessageW(byref(msg), None, 0, 0, 1):
				windll.user32.TranslateMessage(byref(msg))
				windll.user32.DispatchMessageW(byref(msg))
		return winKernel.GetExitCodeProcess(sei.hProcess)
	finally:
		winKernel.closeHandle(sei.hProcess)


class CommandFlags(str, Enum):
	ComServer = "c"
	RDP = "r"
	Citrix = "x"


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
		persistent: bool = False,
		localMachine: bool = False,
		architecture: Architecture = DEFAULT_ARCHITECTURE
):
	atexit.unregister(dllInstall)
	path = getDllPath(architecture)
	command = ""
	if rdp:
		command += CommandFlags.RDP
	if citrix:
		command += CommandFlags.Citrix
	if comServer:
		command += CommandFlags.ComServer
		if install:
			command += f" {COM_CLS_CHANNEL_NAMES_VALUE_BRAILLE} {COM_CLS_CHANNEL_NAMES_VALUE_SPEECH}"
	cmdLine = ["/s", f"/i:\"{command}\"", "/n"]
	if not install:
		cmdLine.append("/u")
	cmdLine.append(path)
	res = execRegsrv(subprocess.list2cmdline(cmdLine), architecture, localMachine)
	if install and not persistent:
		atexit.register(
			dllInstall,
			not install,
			comServer,
			rdp,
			citrix,
			localMachine=localMachine,
			architecture=architecture
		)
	return res
