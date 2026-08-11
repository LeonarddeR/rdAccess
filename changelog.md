* When remote speech is switched on automatically, it now keeps speaking after a configuration profile switch. Previously, NVDA fell back to the synthesizer you have configured as soon as a profile was activated, for example when you moved to an application with its own profile.
* Renamed the option "Automatically recover remote speech after connection loss" to "Automatically switch to remote speech when available", which better describes what it does.
* Fixed frequent errors on the remote system when automatic language switching was enabled while using the remote synthesizer. Reporting of unsupported languages now reflects the languages supported by the speech synthesizer on the client.
* On ARM64 versions of Windows, remote desktop clients that run under x64 emulation can now use RDAccess.
* Adapted to the braille input changes introduced in NVDA 2026.3.
