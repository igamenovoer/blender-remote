# HEADER
- **Created**: 2025-12-16
- **Modified**: 2025-12-17
- **Summary**: CLI design for installing Python packages into the Blender Python environment via `blender-remote-cli`, supporting both online and offline (air-gapped) Blender hosts using RPC.

# Remote Package Installation (`blender-remote-cli pkg ...`)

This document proposes the CLI surface for remotely installing Python packages into Blender’s embedded Python environment using the existing RPC capability (execute Python code in Blender) and without requiring SSH or direct file transfer.

The key problem is supporting both:
- **Online remote** Blender hosts (can reach PyPI / an index server), and
- **Offline remote** Blender hosts (air-gapped, no internet), where the controller machine may still have internet and can stage wheels for transfer.

This design is based on `context/hints/howto-install-packages-on-offline-remote-python-via-rpc.md`.

## Goals

- Provide a dedicated `pkg` command group: `blender-remote-cli pkg ...`.
- Install packages into the remote Blender Python **site-packages** (the interpreter’s default install location).
- Support offline installs by:
  1) discovering remote Python/platform details,
  2) downloading wheels on the controller machine,
  3) transferring wheels to the remote via RPC (chunked),
  4) installing with `pip --no-index --find-links`.
- Bootstrap `pip` on the remote Blender Python if missing (prefer `ensurepip`, otherwise `get-pip.py` transfer).
- Provide an “escape hatch” for advanced users to run arbitrary `pip` commands remotely.

## Non-goals (v1)

- Building wheels for packages without compatible wheels (cross-compilation/build farm is out of scope).
- Managing Blender “Extensions” (Blender 4.2+) as a package system.
- Supporting fully minimal Python interpreters missing stdlib modules (`subprocess`, `zipfile`, `ssl`). Blender’s Python is expected to be complete.

## Terminology

- **Controller**: the machine running `blender-remote-cli`.
- **Remote**: the machine running Blender + `BLD_Remote_MCP` (may be the same host as the controller).
- **Wheelhouse**: a directory of wheels used for offline installation.

## Design Overview

### Installation target (default)

Packages are installed into the remote Blender Python environment’s **site-packages** using pip’s default behavior (no `--target` and no alternate install locations).

Rationale: keep the feature narrowly scoped and predictable: “install into Blender’s Python”, not “manage multiple import locations”.

Note: if the Blender Python site-packages directory is not writable on the remote machine, installation will fail and the user must fix permissions (e.g., run Blender with sufficient rights or adjust the remote environment).

### PIP invocation strategy

Run `pip` using the Python executable exposed by Blender as `sys.executable`, including Blender’s recommended leading args:

- `python_exe = sys.executable`
- `python_args = bpy.app.python_args`
- `subprocess.run([python_exe, *python_args, "-m", "pip", ...])`

Fallback for older Blender versions: if `hasattr(bpy.app, "binary_path_python")` and it’s non-empty, prefer it.

Rationale: the Blender Python API documents `bpy.app.python_args` as the leading arguments to use when calling Python directly (via `sys.executable`).

References:
- Blender Python API: `bpy.app.python_args` (`https://docs.blender.org/api/current/bpy.app.html#bpy.app.python_args`)
- Blender Python API: `bpy.app.online_access` (`https://docs.blender.org/api/current/bpy.app.html#bpy.app.online_access`)

### Online vs offline mode selection

`pkg install` has two modes:

- **Online (default):** when `--remote-wheelhouse` is not provided, run `pip install ...` on the remote (uses remote network access and remote index configuration).
- **Offline:** when `--remote-wheelhouse PATH` is provided, install using `pip install --no-index --find-links <remote-wheelhouse> ...` and do not attempt any network access.

If the remote has no internet access (or Blender disallows it via `bpy.app.online_access`), the online mode will fail; pre-seed a wheelhouse via `pkg push` and use `--remote-wheelhouse`.

`pkg info` reports Blender’s online-access preference (`bpy.app.online_access` when available) and may additionally run a small probe (e.g. `urllib.request.urlopen("https://pypi.org", timeout=5)`) to detect network reachability.

## CLI Shape

### `pkg` (command group)

High-level package management for Blender Python.

Common options (supported on each subcommand in v1, consistent with existing CLI style):
- `--port INTEGER`: override MCP port (defaults to config `mcp_service.default_port`).

### `pkg info`

Print remote Python environment details needed for packaging decisions.

**Usage**
```bash
blender-remote-cli pkg info [OPTIONS]
```

**Output (human-readable by default)**
- Blender version (if available)
- Python version (major.minor.patch)
- `sys.platform`, machine/arch
- `sys.executable` and `bpy.app.python_args`
- Site-packages location(s) (e.g. `site.getsitepackages()`) and whether they’re writable
- `pip` availability/version (if present)
- `bpy.app.online_access` (when available) and internet probe result
- Recommended `pip download` args for preparing an offline wheelhouse (e.g. `--platform win_amd64 --python-version 311`)

**Options**
- `--json`: print a single, syntax-correct JSON object to stdout (no extra human text), suitable for scripting/caching.

### `pkg bootstrap`

Ensure `pip` exists on the remote Blender Python.

**Usage**
```bash
blender-remote-cli pkg bootstrap [OPTIONS]
```

**Behavior**
1. If `pip` is already usable (`python -m pip --version`), no-op.
2. Try `python -m ensurepip --upgrade`.
3. If `ensurepip` fails:
   - If controller has internet, download `get-pip.py` and transfer it to remote, then run it.
   - Otherwise, instruct user to provide `--get-pip PATH`.

**Options**
- `--method auto|ensurepip|get-pip` (default: `auto`)
- `--get-pip PATH`: local path to a `get-pip.py` to transfer (for controller-offline scenarios)
- `--upgrade`: attempt to upgrade pip after bootstrapping

### `pkg install`

Install one or more packages into the remote Blender Python environment.

This is a convenience wrapper around `pkg pip`. Anything `pkg install` can do can also be done using `pkg pip`.

**Usage**
```bash
blender-remote-cli pkg install [OPTIONS] PACKAGE_SPEC...
```

**Package specs**
- Online installs accept package names with optional PEP 440 version constraints, e.g. `requests`, `requests==2.31.0`, `numpy<2`.
- For anything more complex (VCS URLs, local paths, `-r requirements.txt`, custom indexes/proxies, etc.), use `pkg pip`.

**Core options**
- `--upgrade`: pass `--upgrade` to pip
- `--force-reinstall`: pass `--force-reinstall` to pip
- `--no-deps`: pass `--no-deps` to pip
- `--remote-wheelhouse PATH`: install offline from a remote wheelhouse (implies `--no-index --find-links <remote-wheelhouse>`); wheelhouse contents are treated as a persistent cache (clear with `pkg purge-cache`)

**Relationship to `pkg pip`**
- Online: `pkg install numpy` is equivalent to `pkg pip -- install numpy`
- Offline: `pkg install numpy --remote-wheelhouse /tmp/wheels` is equivalent to `pkg pip -- install --no-index --find-links /tmp/wheels numpy`

**Examples**

Online remote:
```bash
blender-remote-cli pkg install numpy
blender-remote-cli pkg install requests==2.31.0 numpy<2
```

Offline remote (explicit wheelhouse workflow):
```bash
# Create a wheelhouse that matches the remote (use `pkg info --json` for the tags)
python -m pip download -d ./wheelhouse --only-binary=:all: --platform <PLATFORM_TAG> --python-version <PYXY> --implementation cp numpy

# Upload wheels once
blender-remote-cli pkg push ./wheelhouse --remote-wheelhouse /tmp/blender-remote/wheels

# Install from the uploaded wheelhouse
blender-remote-cli pkg install numpy --remote-wheelhouse /tmp/blender-remote/wheels
```

### `pkg push`

Transfer a local wheelhouse (or wheel files) to the remote for offline installs.

**Usage**
```bash
blender-remote-cli pkg push [OPTIONS] WHEELHOUSE_OR_WHL...
```

**Options**
- `--remote-wheelhouse PATH`: remote directory to write wheels into (used later by `pkg install --remote-wheelhouse ...`); treated as a persistent cache (clear with `pkg purge-cache`)
- `--chunk-size BYTES`: upload chunk size (default: 5 MiB)

### `pkg purge-cache`

Remove all files in the remote wheelhouse (offline cache).

This does **not** uninstall packages from Blender’s site-packages; it only removes cached wheels/files used for offline installation.

**Usage**
```bash
blender-remote-cli pkg purge-cache [OPTIONS]
```

**Options**
- `--remote-wheelhouse PATH`: remote wheelhouse directory to purge (must match the wheelhouse used for `pkg push` / `pkg install --remote-wheelhouse`)
- `--yes`: skip confirmation

### `pkg pip` (escape hatch)

Run arbitrary `pip` commands on the remote Blender Python (primarily for debugging).

`pkg install` is a convenience wrapper for the common `pip install` cases; `pkg pip` is the general mechanism.

**Usage**
```bash
blender-remote-cli pkg pip [OPTIONS] -- PIP_ARGS...
```

Examples:
```bash
blender-remote-cli pkg pip -- list
blender-remote-cli pkg pip -- show numpy
```

## User Workflows

### 1) Remote has internet

```bash
blender-remote-cli pkg info
blender-remote-cli pkg bootstrap
blender-remote-cli pkg install numpy
```

### 2) Remote is offline, controller has internet

Or explicit staged workflow (reusable local wheelhouse):
```bash
# Create a local wheelhouse (matching the remote)
python -m pip download -d ./wheelhouse --only-binary=:all: --platform <PLATFORM_TAG> --python-version <PYXY> --implementation cp numpy requests

# Upload once
blender-remote-cli pkg push ./wheelhouse --remote-wheelhouse /tmp/blender-remote/wheels

# Install from the uploaded wheelhouse
blender-remote-cli pkg install numpy requests --remote-wheelhouse /tmp/blender-remote/wheels
```

### 3) Remote is offline, controller is also offline

- User must provide a wheelhouse and (if needed) `get-pip.py` locally:
```bash
blender-remote-cli pkg bootstrap --method get-pip --get-pip ./get-pip.py
blender-remote-cli pkg push ./wheelhouse --remote-wheelhouse /tmp/blender-remote/wheels
blender-remote-cli pkg install numpy --remote-wheelhouse /tmp/blender-remote/wheels
```

## Implementation Notes (for later)

### Remote probes and paths

All remote-specific values are derived via a small RPC script:
- Python/platform signature (`sys.platform`, `platform.machine()`, `sys.version_info`)
- Python executable + args (`sys.executable`, `bpy.app.python_args`)
- Site-packages locations and writability (e.g. `site.getsitepackages()`)
- Online access preference (`bpy.app.online_access` when available) + internet probe

### Wheel transfer mechanism

Because `execute_code` RPC messages and/or JSON decoding may have practical size limits, wheel transfer must be chunked:
- Read wheel bytes locally
- Base64 encode in chunks (default 5 MiB pre-b64; configurable via `pkg push --chunk-size`)
- Remote reassembles into a file in `--remote-wheelhouse`

Filename handling must be safe:
- Reject path separators, `..`, and unexpected characters (prevent path traversal).

### Offline installation command

Remote executes:
```bash
<python_exe> <python_args...> -m pip install --no-index --find-links <remote_wheelhouse> <package_specs...>
```

### Reporting and verification

After install, optionally run a lightweight import/version probe remotely:
- `import importlib; importlib.import_module(<name>)`
- Print module `__version__` if available

### Known limitations (communicate in CLI help)

- Wheels must match remote OS/arch and Python major.minor ABI.
- Packages without compatible wheels require building on a matching platform.
- Very large wheels (e.g., torch) may be impractical over RPC; `pkg push --chunk-size` helps but total transfer may still be prohibitive.
