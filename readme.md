# NVDA Remote Desktop

* Authors: [Leonard de Ruijter](https://github.com/leonardder/)
* NVDA compatibility: 2023.1 and later

This add-on adds support to access remote desktop sessions to NVDA.
When installed in NVDA on both the client and the server, speech and braille generated on the server will be spoken and brailled by the client machine.

## Features

* Support for Microsoft Remote Desktop and Citrix XenApp
* Speech and braille output
* Automatic detection of remote braille using NVDA's automatic braille display detection
* Automatic detection of remote speech using a dedicated detection process that can be disabled in NVDA's settings dialog
* Partial support for portable copies of NVDA running on a server (no additional administrative privileges required for Microsoft Remote Desktop)
* Full support for portable copies of NVDA running on a client (no additional administrative privileges required to install the add-on)
* Multiple active client sessions at the same time
* Remote desktop instantly available after NVDA start
* Ability to control specific synthesizer and braille display settings without leaving the remote session

## Configuration

After installation, the NVDA Remote Desktop add-on can be configured using NVDA's settings dialog, which can be accessed from the NVDA Menu by choosing Preferences > Settings...
After that, choose the Remote Desktop category.

This dialog contains the following settings:

### Use NVDA RD for

This group of radio buttons controls the operating mode of the add-on. You can choose between:

* Incoming connections (Remote Desktop Server): Choose this option if the current instance of NVDA is running on a remote desktop server
* Outgoing connections (Remote Desktop Client): Choose this option if the current instance of NVDA is running on a remote desktop client that connects to one or more servers
* Bidirectional connections (Remote Desktop Server and Client): Choose this option if you want to support both scenarios.
You want this if your system can be controlled using Remote Desktop (server) and also acts as a controller (client). This is the case on a so called [Jump Server](https://en.wikipedia.org/wiki/Jump_server), for example.

The default option is Bidirectional Connections to ensure a smooth start with the add-on. You are however encouraged to switch to server or client mode when possible.

### Automatically recover remote speech after connection loss

This option is only available in server mode. It ensures that the connection will automatically be re-established when the Remote Speech synthesizer is active and the connection is lost.
The behavior is very similar to that of braille display auto detection.
This also clarifies why there is only such an option for speech.
The reconnection of the Remote Braille display is automatically handled when choosing the Automatic option from the Braille Display Selection dialog.

This option is enabled by defalt. You are strongly encouraged to leave this option enabled if the Remote Desktop server has no audio output.

### Persist client support when exiting NVDA

This client option is only available on installed copies of NVDA.
When enabled, it ensures that the client portion of NVDA is loaded in your remote desktop client, even when NVDA is not running.

To use the client portion of NVDA Remote Desktop, several changes have to be maede in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user.
These changes don't require administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded, and undo these changes when exiting NVDA.
This ensures that the add-on is fully compatible with portable versions of NVDA.
To allow for this scenario, this option is disabled by default.
However, if you are running an installed copy and you are the only user of the system, you are advised to enable this option to ensure smooth operation in case NVDA started or is not active when connecting to a remote system.

### Enable Microsoft Remote Desktop support

This option is enabled by default and ensures that the client portion of NVDA Remote Desktop is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
Unless persistent client support is enabled by enabling the previous option, these changes will be automatically undone when exiting NVDA.

### Enable Citrix Workspace support

This option is enabled by default and ensures that the client portion of NVDA Remote Desktop is loaded in the Citrix Workspace app when starting NVDA.
Unless persistent client support is enabled by enabling the previous option, these changes will be automatically undone when exiting NVDA.

This option is only available in the following cases:

* Citrix Workspace is installed. Note that the Windows Store version of the app is not supported due to limitations in that app itself
* It is possible to register NVDA Remote Desktop under the current user context. After installing the app, you have to start a remote session once to make this possible

## Citrix specific instructions

There are some important points of attention when using NVDA Remote Desktop with the Citrix Workspace app.

### Client side requirements

1. The Windows Store variant of the app is *not* supported.

2. After installing Citrix Workspace, you have to start a remote session once to allow NVDA Remote Desktop registering itself. The reason behind this is that the application copies the system configuration to the user configuration when it establishes a session for the first time. After that, NVDA Remote Desktop can register itself under the current user context.

### Server side requirement

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so called virtual channel allow list. This means that third party virtual channels, including the channel required bij NVDA Remote Desktop, is not allowed by default. For more information, [see this Citrix blog post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Explicitly allowing the RdPipe channel required by NVDA Remote Desktop is not yet tested. For now, it is probably your best bet to disable the allow list altogether. If your system administrator is unhappy with this, feel free to [open an issue]()

## Todo list

* [ ] Test client side support for Vmware Horizon
* [ ] Test explicitly allowing the RdPipe channel in the [Virtual Channel Allow List](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/policies/reference/ica-policy-settings/virtual-channel-allow-list-policy-settings.html) ([Issue #1](https://github.com/leonardder/nvdaRd/issues/1))
* [ ] Secure desktop support
* [ ] Improve stability

## External components

This add-on relies on [RD Pipe](https://github.com/leonardder/rd_pipe-rs), a library written in Rust backing the remote desktop client support.
RD Pipe is redistributed as part of this add-on under the terms of [version 3 of the GNU Affero General Public License](https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE) as
published by the Free Software Foundation.
