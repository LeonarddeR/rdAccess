# RDAccess: Remote Desktop Accessibility

* Authors: [Leonard de Ruijter][1]
* Download [latest stable version][2]
* NVDA compatibility: 2026.1 and later

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

## Changelog

### Version 2.0.3

* Caps lock synchronization on the client now relies on NVDA 2026.3, which lets RDAccess tell caps lock presses fed back by the remote desktop client apart from real key presses. Synchronization therefore also works when the session is not full screen but Windows key combinations are applied on the remote computer, and when the NVDA setting "Handle keys from other applications" is disabled. The client side of the synchronization requires NVDA 2026.3 or later and is no longer available on older versions of NVDA; the server side keeps working on every supported version.

### Version 2.0.2

* Fixed caps lock going out of sync between the client and the server when both NVDA instances use caps lock as an NVDA modifier key. Quickly repeated caps lock presses in a full screen session no longer toggle caps lock on the client, and when caps lock is really toggled within the session, the client now follows as soon as the session loses focus. This behavior is controlled by the new setting "Synchronize the caps lock key between client and server", which is enabled by default and needs to be enabled on both the client and the server to work correctly. Note that with the setting "Handle keys from other applications" disabled on the client, caps lock can still get out of sync.

### Version 2.0.1

* When remote speech is switched on automatically, it now keeps speaking after a configuration profile switch. Previously, NVDA fell back to the synthesizer you have configured as soon as a profile was activated, for example when you moved to an application with its own profile.
* Renamed the option "Automatically recover remote speech after connection loss" to "Automatically switch to remote speech when available", which better describes what it does.
* Fixed frequent errors on the remote system when automatic language switching was enabled while using the remote synthesizer. Reporting of unsupported languages now reflects the languages supported by the speech synthesizer on the client.
* On ARM64 versions of Windows, remote desktop clients that run under x64 emulation can now use RDAccess.
* Adapted to the braille input changes introduced in NVDA 2026.3.

### Version 2.0

* Speech and braille coming from the remote system are now presented sooner, which makes working in a remote session feel more responsive.
* When starting a remote server instance of NVDA, braille is now shown as soon as a remote session connects, instead of only after the first keypress or focus change.
* Fixed a freeze when switching away from the remote synthesizer or braille display while a session was disconnecting.
* RDAccess now exchanges speech and braille using a new protocol modeled on the one used by NVDA's built-in Remote Access. It is more robust and no longer relies on the pickle format that a compromised remote system could abuse. The protocol version is chosen automatically, so a client and a server running different versions of RDAccess still work together.
* The minimum compatible NVDA version is now 2026.1. Removed support for earlier versions.
* Adapted to the braille changes introduced in NVDA 2026.3.
* Updated RD Pipe dependency to version 0.9.0.
* RDAccess is now licensed under the GNU General Public License version 2 or later.

### Version 1.7.1

* Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.

### Version 1.7

* Removed secure desktop support.
* Added a client option "Incoming speech pitch change percentage" to shift the pitch of speech rendered from a remote NVDA, making remote and local speech audibly distinguishable.

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
1. The remote system should automatically start speaking using the local speech synthesizer.
   If not, in the NVDA instance on the server, select the remote speech synthesizer from NVDA's synthesizer selection dialog.
1. To use braille, enable automatic braille display detection using the braille display selection dialog.

## Configuration

After installation, the RDAccess add-on can be configured using NVDA's settings dialog, accessible from the NVDA Menu by choosing Preferences > Settings...
Then, choose the Remote Desktop category.

This dialog contains the following settings:

### Enable Remote Desktop Accessibility for

This list of checkboxes controls the operating mode of the add-on.
Choose between:

* Incoming connections (Remote Desktop Server): Choose this option if the current instance of NVDA is running on a remote desktop server.
* Outgoing connections (Remote Desktop Client): Choose this option if the current instance of NVDA is running on a remote desktop client that connects to one or more servers.

To ensure a smooth start with the add-on, all options are enabled by default.
However, you are encouraged to disable server or client mode as appropriate.

### Synchronize the Caps Lock Key between Client and Server

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system whenever it captures the keyboard, for example in a full screen session.
When this option is enabled on the client, these fed back caps lock presses no longer toggle caps lock on the client.
When it is enabled on the server, the server reports its caps lock state to the client, which applies it as soon as the remote session loses focus.
For correct behavior, this option needs to be enabled on both the client and the server; it is enabled by default on both.
On the client, this option requires NVDA 2026.3 or later; the server side works with every NVDA version supported by the add-on.

Note that while a remote desktop session window has focus, caps lock presses sent by other software, such as NVDA Remote Access, are suppressed on the client as well.

### Automatically Switch to Remote Speech when Available

This option is only available in server mode.
It ensures that Remote Speech is activated as soon as a remote desktop client offers it, similar to braille display auto-detection, and that the connection is automatically re-established when it is lost.
While Remote Speech is active this way, your configured synthesizer is left untouched, and switching configuration profiles no longer falls back to it.

This option is enabled by default.
It is strongly encouraged to leave this option enabled if the Remote Desktop server has no audio output.

### Allow Remote System to Control Driver Settings

When enabled in the client, this option allows you to control driver settings (such as synthesizer voice and pitch) from the remote system.
Changes made on the remote system will automatically reflect locally.

### Persist Client Support When Exiting NVDA

This client option, available on installed copies of NVDA, ensures that the client portion of NVDA is loaded in your remote desktop client even when NVDA is not running.

To use the client portion of RDAccess, changes need to be made in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user, requiring no administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded and undo these changes when exiting NVDA, ensuring compatibility with portable versions of NVDA.

This option is disabled by default.
However, if you are running an installed copy and you are the only user of the system, it is advised to enable this option for smooth operation when connecting to a remote system after NVDA starts.

### Enable Default Remote Desktop Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
This is also required for VMware Horizon, Parallels RAS, Azure Virtual Desktop. etc.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

### Enable Citrix Workspace Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Citrix Workspace app when starting NVDA.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

This option is available only under the following conditions:

* Citrix Workspace is installed.
  Note that the Windows Store version of the app is not supported due to limitations in the app itself.
* It is possible to register RDAccess under the current user context.
  After installing the app, you have to start a remote session once to enable this.

### Notify of connection changes with

This combo box allows you to control notifications received when a remote system opens or closes the remote speech or braille connection.
You can choose between:

* Off (No notifications)
* Messages (e.g. "Remote braille connected")
* Sounds
* Both messages and sounds

### Incoming Speech Pitch Change Percentage

This client option shifts the pitch of speech rendered locally when it originates from a remote NVDA, making remote and local speech audibly distinguishable.

The value is a percentage between -100 and 100.
Positive values raise pitch, negative values lower it.
A value of 0 disables the shift.
The default is 10.

The shift is applied only when the local synthesizer supports pitch commands; synthesizers without pitch support are unaffected.

### Open diagnostics report

This button opens a browsable message with JSON output containing several diagnostics that can possibly aid in debugging.
When [filing an issue at GitHub][4], you might be asked to provide this report.

## Citrix Specific Instructions

There are important points to note when using RDAccess with the Citrix Workspace app:

### Client-Side Requirements

1. The Windows Store variant of the app is *not* supported.
1. After installing Citrix Workspace, you need to start a remote session once to let RDAccess register itself.
   This occurs because the application copies system settings to user settings during the initial session setup.
   Following this, RDAccess can register itself under the current user context.

### Server-Side Requirement

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so-called virtual channel allow list, restricting third-party virtual channels, including the channel required by RDAccess, by default.
For more information, [see this Citrix blog post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Explicitly allowing the RdPipe channel required by RDAccess is not yet tested.
For now, it is best to disable the allow list altogether.
If your system administrator has concerns, feel free to [address the issue here][3].

## Issues and Contributing

To report an issue or contribute, refer to [the issues page on Github][4].

## External Components

This add-on relies on [RD Pipe][5], a library written in Rust backing the remote desktop client support.
RD Pipe is redistributed as part of this add-on under the terms of [version 3 of the GNU Affero General Public License][6].

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
