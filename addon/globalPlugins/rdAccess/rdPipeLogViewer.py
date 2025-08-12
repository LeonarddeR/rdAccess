# RDAccess: Remote Desktop Accessibility for NVDA
# Copyright 2023 Leonard de Ruijter <alderuijter@gmail.com>
# License: GNU General Public License version 2.0

import typing

import addonHandler
from gui import logViewer

if typing.TYPE_CHECKING:
	from ...lib import rdPipe
else:
	addon: addonHandler.Addon = addonHandler.getCodeAddon()
	rdPipe = addon.loadModule("lib.rdPipe")


class RdPipeLogViewer(logViewer.LogViewer):
	"""The RDAccess log viewer GUI."""

	def __init__(self, parent):
		super().__init__(parent)
		# Translators: The title of the RdPipe Log Viewer
		self.SetTitle(_("RdPipe Log Viewer"))

	def refresh(self, evt=None):  # noqa: ARG002
		# Ignore if log is not initialized
		if not rdPipe.logFileExists():
			return
		pos = self.outputCtrl.GetInsertionPoint()
		# Append new text to the output control which has been written to the log file since the last refresh.
		try:
			with open(rdPipe.LOG_FILE_PATH, encoding="UTF-8") as f:
				f.seek(self._lastFilePos)
				self.outputCtrl.AppendText(f.read())
				self._lastFilePos = f.tell()
				self.outputCtrl.SetInsertionPoint(pos)
		except OSError:
			pass
