* Speech and braille coming from the remote system are now presented sooner, which makes working in a remote session feel more responsive.
* When starting a remote server instance of NVDA, braille is now shown as soon as a remote session connects, instead of only after the first keypress or focus change.
* Fixed a freeze when switching away from the remote synthesizer or braille display while a session was disconnecting.
* RDAccess now exchanges speech and braille using a new protocol modeled on the one used by NVDA's built-in Remote Access. It is more robust and no longer relies on the pickle format that a compromised remote system could abuse. The protocol version is chosen automatically, so a client and a server running different versions of RDAccess still work together.
* The minimum compatible NVDA version is now 2026.1. Removed support for earlier versions.
* Adapted to the braille changes introduced in NVDA 2026.3.
* Updated RD Pipe dependency to version 0.9.0.
* RDAccess is now licensed under the GNU General Public License version 2 or later.
