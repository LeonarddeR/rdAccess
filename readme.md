# RDAccess: Remote Desktop Accessibility

* Authors: [Leonard de Ruijter][1]
* Download [latest stable version][2]
* NVDA compatibility: 2023.2 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support to access remote desktop sessions to NVDA using Microsoft Remote Desktop, Citrix or VMware Horizon.
When installed in NVDA on both the client and the server, speech and braille generated on the server will be spoken and brailled by the client machine.
This enables a user experience where managing a remote system feels just as performant as operating the local system.

## Features

* Support for Microsoft Remote Desktop, Citrix and VMware Horizon
* Speech and braille output
* Automatic detection of remote braille using NVDA's automatic braille display detection
* Automatic detection of remote speech using a dedicated detection process that can be disabled in NVDA's settings dialog
* Support for portable copies of NVDA running on a server (additional configuration required for Fitrix)
* Full support for portable copies of NVDA running on a client (no additional administrative privileges required to install the add-on)
* Multiple active client sessions at the same time
* Remote desktop instantly available after NVDA start
* Ability to control specific synthesizer and braille display settings without leaving the remote session
* Ability to use speech and braille from the user session when accessing secure desktops

## Changelog
### Version 1.1

- Added support for NVDA 2023.3 style device registration for automatic detection of braille displays [#11](https://github.com/leonardder/rdAccess/pull/11)

### Version 1.0

Initial stable release.

## Getting started

1. Install RDAccess in both a client and server copy of NVDA.
1. The remote system should automatically start speaking using the local speech synthesizer. If not, in the NVDA instance on the server, select the remote speech synthesizer from NVDA"s synthesizer selection dialog.
1. To use braille, enable automatic braille display detection using the braille display selection dialog.

## Configuration

After installation, the RDAccess add-on can be configured using NVDA's settings dialog, which can be accessed from the NVDA Menu by choosing Preferences > Settings...
After that, choose the Remote Desktop category.

This dialog contains the following settings:

### Enable remote desktop accessibility for

This list of check boxes controls the operating mode of the add-on. You can choose between:

* Incoming connections (Remote Desktop Server): Choose this option if the current instance of NVDA is running on a remote desktop server
* Outgoing connections (Remote Desktop Client): Choose this option if the current instance of NVDA is running on a remote desktop client that connects to one or more servers
* Secure Desktop pass through: : Choose this option if you want to use braille and speech from the user instance of NVDA when accessing the secure desktop. Note that for this to work, you need to make the RDAccess add-on available on the secure desktop copy of NVDA. For this, choose "Use currently saved settings during sign-in and on secure screens (requires administrator privileges)" in NVDA's general settings.
To ensure a smooth start with the add-on, all options are enabled by default. You are however encouraged to disable server or client mode as appropriate.

### Automatically recover remote speech after connection loss

This option is only available in server mode. It ensures that the connection will automatically be re-established when the Remote Speech synthesizer is active and the connection is lost.
The behavior is very similar to that of braille display auto detection.
This also clarifies why there is only such an option for speech.
The reconnection of the Remote Braille display is automatically handled when choosing the Automatic option from the Braille Display Selection dialog.

This option is enabled by defalt. You are strongly encouraged to leave this option enabled if the Remote Desktop server has no audio output.

### Allow remote system to control driver settings

This client option, when enabled, allows you to control driver settings (such as synthesizer voice and pitch) from the remote system.
This is especially useful when you have difficulties accessing the local NVDA menu when controlling a remote system.
Changes performed on the remote system will automatically be reflected locally.

While enabling this option implies some performance degradation, you are yet advised to enable it.
When this option is disabled, speech synthesizer ppitch changes for capitals don't work.

### Persist client support when exiting NVDA

This client option is only available on installed copies of NVDA.
When enabled, it ensures that the client portion of NVDA is loaded in your remote desktop client, even when NVDA is not running.

To use the client portion of RDAccess, several changes have to be maede in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user.
These changes don't require administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded, and undo these changes when exiting NVDA.
This ensures that the add-on is fully compatible with portable versions of NVDA.

This option is disabled by default.
However, if you are running an installed copy and you are the only user of the system, you are advised to enable this option.
This ensures smooth operation in case NVDA is not active when connecting to a remote system and is then started afterwards.

### Enable Microsoft Remote Desktop support

This option is enabled by default and ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
Unless persistent client support is enabled by enabling the previous option, these changes will be automatically undone when exiting NVDA.

### Enable Citrix Workspace support

This option is enabled by default and ensures that the client portion of RDAccess is loaded in the Citrix Workspace app when starting NVDA.
Unless persistent client support is enabled by enabling the previous option, these changes will be automatically undone when exiting NVDA.

This option is only available in the following cases:

* Citrix Workspace is installed. Note that the Windows Store version of the app is not supported due to limitations in that app itself
* It is possible to register RDAccess under the current user context. After installing the app, you have to start a remote session once to make this possible

## Citrix specific instructions

There are some important points of attention when using RDAccess with the Citrix Workspace app.

### Client side requirements

1. The Windows Store variant of the app is *not* supported.
2. After installing Citrix Workspace, you have to start a remote session once to allow RDAccess registering itself. The reason behind this is that the application copies the system configuration to the user configuration when it establishes a session for the first time. After that, RDAccess can register itself under the current user context.

### Server side requirement

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so called virtual channel allow list. This means that third party virtual channels, including the channel required by RDAccess, is not allowed by default. For more information, [see this Citrix blog post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Explicitly allowing the RdPipe channel required by RDAccess is not yet tested. For now, it is probably your best bet to disable the allow list altogether. If your system administrator is unhappy with this, feel free to [drop a line in the devoted issue][3]

## Issues and contributing

If you want to report an issue or contribute, take a look at [the issues page on Github][3]

## External components

This add-on relies on [RD Pipe][4], a library written in Rust backing the remote desktop client support.
RD Pipe is redistributed as part of this add-on under the terms of [version 3 of the GNU Affero General Public License][5] as
published by the Free Software Foundation.

[[!tag dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
