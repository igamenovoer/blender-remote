# HEADER
- **Created**: 2025-12-18
- **Modified**: 2025-12-18
- **Summary**: Design for a new `blender-remote-cli addon ...` command group that manages **user add-ons** for a **local** Blender installation by combining direct filesystem operations with one-shot Blender background runs to persist preferences (enable/disable).

# Local Add-on Management (`blender-remote-cli addon ...`)

This document proposes the CLI surface and behavioral contract for managing
Blender **user add-ons** for a **local** Blender installation.

The design is inspired by the exploratory script in `tmp/blender-addon-mgr.py`,
but is scoped and integrated into `blender-remote-cli` conventions:
- no MCP/RPC
- no remote file transfer
- run Python inside Blender via `<blender> --background`, not via a standalone `python.exe`

## Goals

- Provide a first-class CLI group for add-on lifecycle operations:
  - install from local folder/zip/py
  - enable/disable with persisted user preferences
  - list and inspect installed add-ons (user-only by default)
  - uninstall safely (user add-ons only by default)
- Work with a locally managed Blender installation (configured via `blender-remote-cli init`).
- Support scripting/automation via `--json` output that is robust against Blender log noise.
- Avoid relying on Blender internals that change across versions, when a more stable option exists.

## Non-goals (v1)

- Managing Blender “Extensions” (Blender 4.2+) as a separate ecosystem/package manager.
- Downloading add-ons from the internet or resolving add-on dependencies.
- Managing add-ons inside a currently running interactive Blender instance.
- Managing add-ons on a remote machine.
- Editing arbitrary Blender preferences beyond add-on enable/disable state.

## Terminology

- **Blender installation**: the local Blender executable + its directories, configured by `blender-remote-cli init`.
- **User add-ons directory**: the directory where Blender installs user add-ons (typically under the user config/scripts area).
- **Add-on module name**: the Python module name Blender uses to identify an add-on (folder name for package add-ons, filename stem for single-file add-ons).

## Key Assumptions

- `blender-remote-cli` has direct filesystem access to the Blender installation.
- When Blender Python execution is required (preferences, addon_utils), we launch Blender in background mode:
  - `<blender-executable> --background --python <script.py> -- ...`
- We do **not** depend on a standalone Python interpreter embedded in Blender.

## Design Overview

`addon` is a new top-level command group:

```bash
blender-remote-cli addon [SUBCOMMAND] [OPTIONS]
```

### Blender executable resolution

- Default: read `blender.exec_path` from CLI config (`blender-remote-cli init`).
- If missing: fail with a message instructing the user to run `init`.

Optional future enhancement (not required for v1):
- `blender-remote-cli addon --blender-exec <PATH> ...` as a group-level override.

### Timeouts

- Use `cli.timeout_sec` as the default timeout for Blender background runs.
- Optional future enhancement: per-command `--timeout-sec` override.

### Output discipline (`--json`)

Many Blender invocations print startup noise and logs. For scripting, `addon` must be able
to emit a single, valid JSON value to stdout.

Proposed contract:
- If `--json` is set: `blender-remote-cli` prints exactly one JSON value (object or array) to stdout.
- Any diagnostics go to stderr.
- Internally: Blender-run scripts print the JSON payload between sentinel markers, then the CLI extracts it.

Example sentinels:
- `__BLENDER_REMOTE_JSON_BEGIN__`
- `__BLENDER_REMOTE_JSON_END__`

## CLI Shape

### `addon list`

List add-ons and their state.

**Usage**
```bash
blender-remote-cli addon list [--all] [--json]
```

**Behavior**
- Default: list only add-ons that live under the **user add-ons directory**.
- With `--all`: include add-ons from all script/add-on paths (bundled/system/etc).

**Output (JSON array)**
Each entry should include at least:
- `name` (module name)
- `enabled` (bool)
- `loaded` (bool)
- `version` (best-effort, from `bl_info`)
- `path` (best-effort file path, from module `__file__`)
- `source` classification (`user` | `system` | `bundled` | `unknown`) best-effort

### `addon info`

Inspect a specific add-on.

**Usage**
```bash
blender-remote-cli addon info <ADDON_NAME> [--json]
```

**Behavior**
- If the add-on is not found:
  - human output: show a clear “not found” message and exit non-zero
  - `--json`: print `{}` and exit non-zero (so scripting can distinguish “empty” from success)

**Output (JSON object)**
Includes all fields from `list`, plus extended `bl_info` fields when available:
- `author`, `description`, `category`, `warning`, `doc_url`, `tracker_url`

### `addon install`

Install an add-on from a local source.

**Usage**
```bash
blender-remote-cli addon install <SOURCE> [--enable] [--overwrite/--no-overwrite] [--json]
```

**Supported `SOURCE` types**
- Directory (package add-on)
- `.zip` archive (package add-on)
- `.py` file (single-file add-on)

**Behavior**
- Installation must not require any network.
- Default target: Blender’s **user add-ons directory**.
- `--overwrite` default: `true` (safe, predictable automation). `--no-overwrite` errors if the destination exists.
- `--enable`:
  - After installation, enable the add-on and persist user preferences.
  - If enabling fails, the install may still have succeeded; return a structured error (non-zero exit) that includes whether files were installed.

**Module name resolution**
Avoid brittle heuristics where possible:
- Directory: module name = folder name.
- `.py`: module name = filename stem.
- `.zip`: prefer one of:
  1) inspect archive top-level entry name
  2) fallback to a Blender-based “before/after” module list diff

**Output (JSON object)**
```json
{
  "op": "install",
  "source": "...",
  "module_name": "...",
  "installed_path": "...",
  "enabled": true,
  "warnings": [],
  "errors": []
}
```

### `addon enable` / `addon disable`

Enable/disable an add-on and persist preferences.

**Usage**
```bash
blender-remote-cli addon enable <ADDON_NAME> [--json]
blender-remote-cli addon disable <ADDON_NAME> [--json]
```

**Behavior**
- Always call `save_userpref` after changing state.
- Idempotent: enabling an already-enabled add-on should succeed (same for disable).

**Output (JSON object)**
```json
{"op":"enable","module_name":"...","enabled":true}
```

### `addon uninstall`

Remove a user add-on from disk (and disable it first).

**Usage**
```bash
blender-remote-cli addon uninstall <ADDON_NAME> [--json] [--force]
```

**Safety rules**
- By default, only uninstall if the resolved module path is within the **user add-ons directory**.
- If the add-on resolves outside user add-ons, refuse unless `--force` is provided.
- Uninstall should disable first (best-effort), then remove files.

**Output (JSON object)**
```json
{"op":"uninstall","module_name":"...","disabled":true,"removed":true,"removed_path":"..."}
```

### Optional: `addon paths` (nice-to-have)

Expose add-on paths for debugging.

**Usage**
```bash
blender-remote-cli addon paths [--json]
```

**Output**
- user add-ons directory
- list of add-on search paths
- configured Blender executable path

## Blender-side Implementation Strategy (conceptual)

Certain operations should run “inside Blender” because they depend on `bpy`/`addon_utils`
and must persist preferences safely.

For Blender-run scripts:
- Prefer `--quiet --background` to minimize noise.
- Avoid `--factory-startup` by default for `addon` commands, because it risks ignoring or clobbering user preferences.
- Explicitly call:
  - `bpy.ops.wm.read_userpref()` (best-effort) before changing add-on state
  - `bpy.ops.wm.save_userpref()` after state changes
- Use `addon_utils` for enable/disable and `addon_utils.modules()` + `addon_utils.check()` for listing.

Filesystem operations can be done either:
- directly in the CLI (copy/unzip/remove), using the user add-ons directory discovered from Blender, or
- inside Blender (similar to `tmp/blender-addon-mgr.py`) when it reduces ambiguity.

## User-facing Workflows

### Install and enable an add-on from a folder
```bash
blender-remote-cli addon install ./my_addon --enable
```

### Install from a zip (offline)
```bash
blender-remote-cli addon install ./some_addon.zip --enable
```

### Disable an add-on temporarily
```bash
blender-remote-cli addon disable some_addon
```

### List installed user add-ons
```bash
blender-remote-cli addon list
```

## Security Notes

Installing/enabling an add-on runs arbitrary Python code. This CLI must treat add-ons as
trusted input and should:
- require explicit user intent for install/enable operations (no silent auto-enable)
- clearly surface the target paths and module name in outputs

## Open Questions

- Should `addon install` default to `--enable` for parity with typical UI workflows, or keep it explicit?
- Should uninstall refuse to run if Blender is currently open (to avoid preference races)?
- How aggressively should we normalize the user add-ons directory across platforms/versions (Blender probe vs config)?
- Should we support “install without running Blender” for pure filesystem operations, or always verify via a Blender probe run?

