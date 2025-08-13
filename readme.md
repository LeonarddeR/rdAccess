# RDAccess: Remote Desktop Accessibility

* Authors: [Leonard de Ruijter][1]
* Download [latest stable version][2]
* NVDA compatibility: 2024.1 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support for Microsoft Remote Desktop, Citrix, Parallels RAS, or VMware Horizon remote sessions to NVDA.
When installed on both the client and the server in NVDA, speech and braille generated on the server will be spoken and displayed in braille on the client machine.
This enables a user experience where managing a remote system feels as seamless as operating the local system.

## Features

* Support for Microsoft Remote Desktop (including Azure Virtual Desktop and Microsoft Cloud PC), Citrix, Parallels RAS, and VMware Horizon
* Speech and braille output
* Automatic detection of remote braille using NVDA's automatic braille display detection
* Automatic detection of remote speech using a dedicated detection process that can be disabled in NVDA's settings dialog
* Support for portable copies of NVDA running on a server (additional configuration required for Citrix)
* Full support for portable copies of NVDA running on a client (no additional administrative privileges required to install the add-on)
* Multiple active client sessions simultaneously
* Remote desktop instantly available after NVDA start
* Ability to control specific synthesizer and braille display settings without leaving the remote session
* Ability to use speech and braille from the user session when accessing secure desktops

## Changelog

### Version 1.6

* Documented and improved Parallels RAS support.
* The minimum compatible NVDA version is now 2025.1. Removed support for earlier versions.
* Updated RdPipe dependency.
* Added the ability to configure RdPipe log level.
* Added a viewer for the RdPipe log, available from the settings panel.
* Improved uninstall behavior (no longer raise errors or remove Citrix support when Citrix is not available).

### Version 1.5

* Add the ability to create a debugging diagnostics report by means of a button in the RDAccess settings panel [#23](https://github.com/leonardder/rdAccess/pull/23).
* Support for multi-line braille displays in NVDA 2025.1 and newer [#19](https://github.com/leonardder/rdAccess/pull/13).
* The minimum compatible NVDA version is now 2024.1. Removed support for earlier versions.
* Added client connection notifications [#25](https://github.com/leonardder/rdAccess/pull/25).
* Updated RdPipe dependency.
* Updated translations.

### Version 1.4

* New stable release.

### Version 1.3

* Fixed broken braille display gestures.

### Version 1.2

* Use [Ruff](https://github.com/astral-sh/ruff) as a formatter and linter. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Fixed an issue where NVDA on the client generates an error when pausing speech on the server.
* Fixed support for `winAPI.secureDesktop.post_secureDesktopStateChange`.
* Improved driver initialization on the server.

### Version 1.1

* Added support for NVDA 2023.3 style device registration for automatic detection of braille displays. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Added support for NVDA 2024.1 Alpha `winAPI.secureDesktop.post_secureDesktopStateChange` extension point. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Version 1.0

Initial stable release.

## Getting Started

1. Install RDAccess on both a client and server copy of NVDA.
1. The remote system should automatically start speaking using the local speech synthesizer. If not, in the NVDA instance on the server, select the remote speech synthesizer from NVDA's synthesizer selection dialog.
1. To use braille, enable automatic braille display detection using the braille display selection dialog.

## Configuration

After installation, the RDAccess add-on can be configured using NVDA's settings dialog, accessible from the NVDA Menu by choosing Preferences > Settings...
Then, choose the Remote Desktop category.

This dialog contains the following settings:

### Enable Remote Desktop Accessibility for

This list of checkboxes controls the operating mode of the add-on. Choose between:

* Incoming connections (Remote Desktop Server): Choose this option if the current instance of NVDA is running on a remote desktop server.
* Outgoing connections (Remote Desktop Client): Choose this option if the current instance of NVDA is running on a remote desktop client that connects to one or more servers.
* Secure Desktop pass-through: Choose this option if you want to use braille and speech from the user instance of NVDA when accessing the secure desktop. Note that for this to work, you need to make the RDAccess add-on available on the secure desktop copy of NVDA. For this, choose "Use currently saved settings during sign-in and on secure screens (requires administrator privileges)" in NVDA's general settings.

To ensure a smooth start with the add-on, all options are enabled by default. However, you are encouraged to disable server or client mode as appropriate.

### Automatically Recover Remote Speech after Connection Loss

This option is only available in server mode. It ensures that the connection will automatically be re-established when the Remote Speech synthesizer is active and the connection is lost, similar to braille display auto-detection.

This option is enabled by default. It is strongly encouraged to leave this option enabled if the Remote Desktop server has no audio output.

### Allow Remote System to Control Driver Settings

When enabled in the client, this option allows you to control driver settings (such as synthesizer voice and pitch) from the remote system. Changes made on the remote system will automatically reflect locally.

### Persist Client Support When Exiting NVDA

This client option, available on installed copies of NVDA, ensures that the client portion of NVDA is loaded in your remote desktop client even when NVDA is not running.

To use the client portion of RDAccess, changes need to be made in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user, requiring no administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded and undo these changes when exiting NVDA, ensuring compatibility with portable versions of NVDA.

This option is disabled by default. However, if you are running an installed copy and you are the only user of the system, it is advised to enable this option for smooth operation when connecting to a remote system after NVDA starts.

### Enable Default Remote Desktop Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
This is also required for VMware Horizon, Parallels RAS, Azure Virtual Desktop. etc.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

### Enable Citrix Workspace Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Citrix Workspace app when starting NVDA.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

This option is available only under the following conditions:

* Citrix Workspace is installed. Note that the Windows Store version of the app is not supported due to limitations in the app itself.
* It is possible to register RDAccess under the current user context. After installing the app, you have to start a remote session once to enable this.

### Notify of connection changes with

This combo box allows you to control notifications received when a remote system opens or closes the remote speech or braille connection.
You can choose between:

* Off (No notifications)
* Messages (e.g. "Remote braille connected")
* Sounds (NVDA 2025.1+)
* Both messages and sounds

Note that sounds are not available on NVDA versions older than 2025.1. Beeps will be used on older versions.

### Open diagnostics report

This button opens a browsable message with JSON output containing several diagnostics that can possibly aid in debugging.
When [filing an issue at GitHub][4], you might be asked to provide this report.

## Citrix Specific Instructions

There are important points to note when using RDAccess with the Citrix Workspace app:

### Client-Side Requirements

1. The Windows Store variant of the app is *not* supported.
1. After installing Citrix Workspace, you need to start a remote session once to let RDAccess register itself. This occurs because the application copies system settings to user settings during the initial session setup. Following this, RDAccess can register itself under the current user context.

### Server-Side Requirement

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so-called virtual channel allow list, restricting third-party virtual channels, including the channel required by RDAccess, by default.
For more information, [see this Citrix blog post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Explicitly allowing the RdPipe channel required by RDAccess is not yet tested. For now, it is best to disable the allow list altogether. If your system administrator has concerns, feel free to [address the issue here][3].

## Issues and Contributing

To report an issue or contribute, refer to [the issues page on Github][4].

## External Components

This add-on relies on [RD Pipe][5], a library written in Rust backing the remote desktop client support.
RD Pipe is redistributed as part of this add-on under the terms of [version 3 of the GNU Affero General Public License][6].

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
