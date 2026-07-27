# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

RDAccess (Remote Desktop Accessibility): NVDA add-on bridging speech and braille between NVDA on a remote-desktop server and NVDA on the client. Supports Microsoft Remote Desktop / AVD / Cloud PC, Citrix Workspace, Parallels RAS, VMware Horizon. Min NVDA 2025.1, Python 3.13.

Sibling source repos (paths relative to this repo):

* `..\nvda` — NVDA source. Look here for any NVDA-side API used by this add-on (`hwIo.ioThread`, `braille`, `synthDriverHandler`, `extensionPoints`, `winBindings.kernel32`, etc.). The add-on imports many internal NVDA modules; check there before guessing signatures.
* `..\rd_pipe-rs` — `rd_pipe.dll` source (Rust). Implements the Windows RDS Dynamic Virtual Channel COM server and bridges each DVC to a named pipe `\\.\pipe\RdPipe\<session>\<channel>`. The DLL is shipped pre-built under `addon/dll/{x86,x64,arm64}/rd_pipe.dll` and registered as in-proc COM server (CLSID `{D1F74DC7-9FDE-45BE-9251-FA72D4064DA3}`) on the **client** side. Channels: `NVDA-SPEECH`, `NVDA-BRAILLE`.

## Build / Lint

Toolchain: `uv` + SCons. Run from repo root.

| Task | Command |
|---|---|
| Install dev deps | `uv sync` |
| Build add-on (`.nvda-addon`) | `uv run scons` |
| Translation template | `uv run scons pot` |
| Merge POT | `uv run scons mergePot` |
| Dev (timestamped) build | `uv run scons dev=1` |
| Lint + format + type check | `uv run prek run --all-files` (ruff + ty, configured in `prek.toml` / `pyproject.toml`) |
| Type check only | `uv run ty check` |
| Clean | `uv run scons -c` |

Git hooks run via **prek** (Rust pre-commit alternative; config in `prek.toml`). Run `uv run prek install -f` once to wire the git hooks.

Unit tests live in `tests/` (stdlib unittest): `uv run python -m unittest discover -s tests -t .`. They run without NVDA by stubbing NVDA runtime modules in `sys.modules` (`tests/_stubs.py`) and reusing the real `baseObject`/`extensionPoints` from the sibling `..\nvda\source` checkout, which must therefore be present. Tests cover `addon/lib/protocol`; integration behavior (pipes, drivers, NVDA core) is still validated manually against NVDA on a real RDP/Citrix session. The suite also runs as a prek hook and as a CI step.

Type checking uses **ty** (`[tool.ty]` in `pyproject.toml`), scoped to `addon/` + `buildVars.py`. NVDA internals are resolved against a sibling `..\nvda\source` checkout, so type checking requires the NVDA source repo alongside this one (CI clones it). `wx` / `serial.win32` resolve from the `wxPython` / `pyserial` dev deps.

Indentation is **tabs** (ruff `indent-style=tab`, `W191` ignored). Line length 110. `from __future__ import annotations` is enforced (`future-annotations = true`).

## Architecture

### Two operating modes (a single NVDA instance can run both)

Configured in `addon/lib/configuration.py` as `OperatingMode` flags. `globalPlugins/rdAccess/__init__.RDGlobalPlugin` chooses what to initialize based on the bitmask.

* **CLIENT** (local NVDA, RDP/Citrix viewer process): registers `rd_pipe.dll` under HKCU so the RDP/Citrix client loads it as a DVC plugin. Watches `\\.\pipe\` for `RdPipe_NVDA-{SPEECH,BRAILLE}*` pipes appearing (created when the server end opens the DVC), and for each pipe spawns a `RemoteSpeechHandler` or `RemoteBrailleHandler`. Output (speech/braille) read from the pipe is rendered on the local synth/display.
* **SERVER** (NVDA inside the remote session): exposes a synth driver (`addon/synthDrivers/remote.py`) and a braille display driver (`addon/brailleDisplayDrivers/remote.py`) that open the DVC end and forward NVDA's speech/braille over it. Server-side speech driver auto-detection runs via `globalPlugins/rdAccess/synthDetect.py` when `recoverRemoteSpeech` is on.

Client-side detection of new pipes uses `directoryChanges.DirectoryWatcher` (ReadDirectoryChangesW) on `\\.\pipe\` with glob `RdPipe_NVDA-*` (`addon/lib/namedPipe.py`).

### Protocol (`addon/lib/protocol/`)

Dual-stack: two wire formats coexist on each pipe, negotiated automatically per connection.

**Protocol v2 (JSON Lines)** — modeled on NVDA core's `_remoteClient` protocol: one UTF-8 JSON object per `\n`-terminated line with a mandatory `"type"` field. Message types are `RdMessageType(StrEnum)` in `messages.py`; names/values mirror `RemoteMessageType` where semantics match (`speak`, `cancel`, `pause_speech`, `tone`, `wave`, `index`, `display`, `braille_input`, `protocol_version`, `ping`), plus RDAccess-specific `attribute_request`/`attribute_value`. `serializer.py` (`RdJSONSerializer`) encodes speech sequences byte-for-byte identically to `_remoteClient.serializer` (`[ClassName, __dict__]` pairs); RDAccess-specific values (DriverSetting family, VoiceInfo, GlobalGestureMap via `export()`/`update()`, `supportedCommands` class-name lists) extend the same convention with explicit per-attribute decode allowlists. Conformance tests (`tests/test_serializerConformance.py`) load `..\nvda\source\_remoteClient\{serializer,protocol}.py` by file path and fail when NVDA core drifts.

**Protocol v1 (legacy, binary + pickle)** — `[driverType:1][command:1][payloadLen:2 LE][payload...]`; `driverType` ∈ `{S, B}`. All v1 byte formats live in `legacy.py`, which translates frames to/from the same value-based messages (`encode/decodeCommandPayload`, `encode/decodeAttributeValue`); pickled payloads pass through `_restrictedUnpickling.RestrictedUnpickler` only.

**Negotiation**: both sides push a `protocolVersion` attribute at connect (client on pipe connect, server after XON). Receive side sniffs the first byte per message (`{` = JSON line, driverType byte = legacy frame; `_onReceive`). Send side stays legacy until the peer is known to be ≥ v2 (explicit version, or any received JSON line), then flips (`_sendJson`) and emits a one-shot `protocol_version` message with a `channel` field validated against the pipe's channel. Old peers never answer the version push, so `defaultValue=1` keeps everything legacy. Legacy removal is planned for a later release.

`RemoteProtocolHandler` (in `protocol/__init__.py`) is the abstract base, used by both driver classes (server side) and handler classes (client side). All dispatch funnels through `_handleMessage(messageType, kwargs)` → `_commandHandlerStore`; the built-in message types (`attribute_request`/`attribute_value`/`protocol_version`/`ping`) are ordinary `@commandHandler` methods on the base, so subclasses can override any message type through the same registry. Sends go through `sendMessage(messageType, **payload)`. Three decorator-driven registries are populated at `__new__` time by introspecting the class:

* `@commandHandler(RdMessageType.X)` → `CommandHandlerStore` — dispatch incoming messages; handlers receive decoded kwargs.
* `@attributeSender(attr)` → `AttributeSenderStore` — return the Python value when peer requests `attr`.
* `@attributeReceiver(attr, defaultValue=…)` → `AttributeValueProcessor` — accept the decoded value when peer pushes `attr`; `.defaultValueGetter` and `.updateCallback` are settable via the returned descriptor. When the decoded value needs no transformation, assign a bare `AttributeReceiver(attr, defaultValue=…)` as a class attribute instead of decorating an identity method.

Attributes are `str`; wildcards are allowed (`*` matched via `fnmatch`) — `_incoming_setting` is the catch-all for `setting_*` attributes used to forward driver settings (voice, pitch, dot-firmness, etc.) bidirectionally.

Incoming messages, attribute receivers and update callbacks all run inline on the device's IO thread, in arrival order. Handlers must therefore never block: anything touching NVDA core state hops via `_queueFunctionOnMainThread` (queues onto `queueHandler.eventQueue`), and calling `getRemoteAttribute`/`_safeWait` on the IO thread raises `RuntimeError` (the reply could never be processed there).

### Handlers (client side, `addon/globalPlugins/rdAccess/handlers/`)

* `_remoteHandler.RemoteHandler` — base, holds an `IoThread`-backed `NamedPipe` IO object, owns a local NVDA `_driver` (synth or braille display) onto which incoming attributes/commands are projected.
* `RemoteSpeechHandler`, `RemoteBrailleHandler` — driverType-specific subclasses. `RemoteBrailleHandler` keeps the local braille handler's display in sync via `extensionPoints` (`pre_writeCells`, `post_setDisplay`, etc.).

### Drivers (server side)

* `addon/synthDrivers/remote.py` — `synthDriverHandler.SynthDriver` subclass that opens the DVC, reflects the remote synth's `supportedSettings`/`availableVoices`/etc. as its own.
* `addon/brailleDisplayDrivers/remote.py` — `braille.BrailleDisplayDriver` subclass; supports auto-detect via the standard NVDA mechanism.

### `rd_pipe.dll` integration (`addon/lib/rdPipe.py`)

`dllInstall(install, comServer, rdp, citrix, architecture=…)` runs `regsvr32 /s [/u] /i:"<flags> NVDA-SPEECH NVDA-BRAILLE" rd_pipe.dll`. Flags follow the rd_pipe-rs `DllInstall` contract:

* `c` COM in-proc server, `r` RDP/MSTS, `x` Citrix (x86 only), `m` HKLM (omit for HKCU).

Citrix support is x86-only (Citrix Workspace is 32-bit), so on AMD64/ARM64 hosts `_updateRegistryForRdPipe` issues two calls: native arch for `r`, x86 DLL for `x`. `isCitrixSupported()` requires both `HKLM\…\CitrixOnlinePluginPackWeb` and a writable `HKCU\…\ICA Client\Engine\Configuration\Advanced\Modules` (the latter only exists after the user has launched a Citrix session at least once).

Persistent vs. transient registration: when `persistentRegistration` is off (default), `atexit` unregisters on NVDA exit — required for portable NVDA copies and unprivileged installs.

### Lifecycle gotchas

* `RDGlobalPlugin.__init__` short-circuits on secure desktop (`isRunningOnSecureDesktop()`); v1.7 dropped secure-desktop support entirely.
* `_handlePostConfigProfileSwitch` diffs old vs. new config to surgically (de)initialize client/server halves and re-register the DLL when the RDP/Citrix flags change. Don't bypass this when adding new config keys.
* `terminate()` on a `RemoteProtocolHandler` sleeps `timeout/10` before closing the pipe — otherwise the remote end can be left in an unrecoverable state. Preserve this when refactoring.

## buildVars / manifest

`buildVars.py` is the single source of truth for add-on metadata (name, version, NVDA min/lastTested, included files). `manifest.ini.tpl` and `manifest-translated.ini.tpl` are rendered by SCons via `site_scons/site_tools/NVDATool`. Bump `addon_version` and `addon_lastTestedNVDAVersion` here, not in the manifest.

## Translations

User-facing strings via `_()` / `pgettext()` / `ngettext()` / `npgettext()` with a preceding `# Translators:` comment. `scons pot` regenerates `addon/locale/<addon>.pot`. Translations are managed via Crowdin (deps `crowdin-api-client` etc. in `pyproject.toml`).
