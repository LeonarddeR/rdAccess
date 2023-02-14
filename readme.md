# NVDA Remote Desktop

* Authors: [Leonard de Ruijter](https://github.com/leonardder/)
* NVDA compatibility: 2023.1 and later

This add-on adds support for remote desktop to NVDA.
When installed in NVDA on both the client and the server, speech and braille generated on the server will be spoken and brailled by the client machine.

## Features

* Support for Microsoft Remote Desktop Protocol and VMware Horizon
* Speech and braille output
* Automatic detection of remote braille using NVDA's automatic braille display detection
* Automatic detection of remote speech using a dedicated detection process that can be disabled in NVDA's settings dialog
* Portable copies of NVDA arunning on a server are fully supported (no additional administrative privileges required to install the add-on)
* Partial support for portable copies of NVDA running on a client (no additional administrative privileges required to install the add-on when using Microsoft Remote Desktop or VMware Horizon)
* Multiple active client sessions at the same time
* Remote desktop instantly available after NVDA start
* Ability to control specific synthesizer and braille display settings without leaving the remote session

## Todo list

* Support for Citrix clients
* Secure desktop support

## External components

This add-on relies on [RD Pipe](https://github.com/leonardder/rd_pipe-rs) a library written in Rust backing the remote desktop client support.
RD Pipe is redistributed as part of this add-on under the terms of [version 3 of the GNU Affero General Public License](https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE) as
published by the Free Software Foundation.
