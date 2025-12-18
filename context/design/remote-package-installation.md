# HEADER
- **Created**: 2025-12-16
- **Modified**: 2025-12-18
- **Summary**: CLI design for managing Python packages in a local Blender installation via `blender-remote-cli`, by running `<blender> --background` to execute Python/pip in Blender’s embedded Python (no direct python.exe reliance, no MCP/RPC).

# Blender Package Management (`blender-remote-cli pkg ...`)

This document proposes a small CLI surface for managing Python packages in Blender’s embedded Python environment.

Key assumption (scope refinement):
- `blender-remote-cli` manages a **local** Blender installation: it has direct access to the Blender executable, can launch/kill it, can read/write its installation directories, and can run Blender’s bundled Python interpreter.
- To run Python code/scripts reliably and future-proof, use the configured Blender executable in background mode: `<blender-executable> --background --python <script.py>`.
- Do not depend on a hardcoded standalone Python executable path inside the Blender installation (layout varies across platforms/versions).

The key problem is supporting both:
- **Online installs** (host can reach PyPI / an index server), and
- **Offline installs** (air-gapped, no internet), where wheels/archives must already exist on the same machine as the Blender installation (staged by the user via any out-of-band method).

## Goals

- Provide a dedicated `pkg` command group: `blender-remote-cli pkg ...`.
- Support installing packages into Blender Python **site-packages** (the interpreter’s default install location) by running Blender in background mode and executing `pip` inside Blender’s embedded Python.
- Support offline installs by:
  1) discovering Blender Python/platform details,
  2) letting the user stage wheels/archives locally (out of scope for this CLI),
  3) installing with `pip --no-index --find-links <path>` (or other pip args).
- Bootstrap `pip` for Blender Python if missing (prefer `ensurepip`, otherwise run a user-provided local `get-pip.py`).
- Provide an “escape hatch” for advanced users to run arbitrary `pip` commands.

## Non-goals (v1)

- Building wheels for packages without compatible wheels (cross-compilation/build farm is out of scope).
- Managing Blender “Extensions” (Blender 4.2+) as a package system.
- Uploading, transferring, or managing files on another machine (wheel transfer, remote cache management, etc.).
- Managing packages by executing `pip` inside a running Blender instance via in-process `bpy` or MCP/RPC.
- Supporting fully minimal Python interpreters missing stdlib modules (`subprocess`, `zipfile`, `ssl`). Blender’s Python is expected to be complete.

## Terminology

- **Blender installation**: the locally managed Blender executable + its installation directories (configured via `blender-remote-cli init`).
- **Blender Python**: the Python interpreter shipped with that Blender installation.
- **Wheelhouse**: a local directory of wheels used for offline installation.

## Design Overview

### Installation target (default)

Packages are installed into Blender Python’s **site-packages** using pip’s default behavior (no `--target` and no alternate install locations).

Rationale: keep the feature narrowly scoped and predictable: “install into Blender’s Python”, not “manage multiple import locations”.

Note: if the Blender Python site-packages directory is not writable, installation will fail and the user must fix permissions (e.g., run with sufficient rights or install Blender in a user-writable location).

### PIP invocation strategy

Run `pip` by launching Blender in background mode and executing a small Python script inside Blender’s embedded Python:

- CLI runs: `<blender-executable> --background --python <tmp_script.py> -- <PIP_ARGS...>`
- The script implements a `python -m pip ...` equivalent in-process (e.g., via `runpy.run_module("pip", run_name="__main__")`) and exits with pip’s return code.

Rationale: avoid relying on Blender’s installation layout for a standalone `python.exe`, while still operating on Blender’s embedded Python environment.

### Online vs offline mode selection

`pkg` does not attempt to detect or enforce online/offline mode. Users control pip’s behavior explicitly via `pkg pip` arguments:

- **Online:** use normal `pip install ...` semantics (host must have internet access and index configuration).
- **Offline:** stage wheels/archives locally, then use `pip install --no-index --find-links <path> ...` (or `pip install /path/to/wheel.whl`).

## CLI Shape

### `pkg` (command group)

High-level package management for Blender Python.

### `pkg info`

Print Blender Python environment details needed for packaging decisions.

**Usage**
```bash
blender-remote-cli pkg info [OPTIONS]
```

**Output (human-readable by default)**
- Blender version (if available)
- Python version (major.minor.patch)
- `sys.platform`, machine/arch
- Blender executable path used for package operations
- Site-packages location(s) (e.g. `site.getsitepackages()`) and whether they’re writable
- `pip` availability/version (if present)
- Recommended `pip download` args for preparing an offline wheelhouse (e.g. `--platform win_amd64 --python-version 311`)

**Options**
- `--json`: print a single, syntax-correct JSON object to stdout (no extra human text), suitable for scripting/caching; the CLI should extract/emit only the JSON even if Blender prints additional logs.

### `pkg bootstrap`

Ensure `pip` exists for Blender Python.

**Usage**
```bash
blender-remote-cli pkg bootstrap [OPTIONS]
```

**Behavior**
1. If `pip` is already usable (equivalent of `python -m pip --version`), no-op.
2. Try ensurepip (equivalent of `python -m ensurepip --upgrade`).
3. If `ensurepip` fails:
   - Require the user to provide a local `get-pip.py` path and run it using Blender Python.

**Options**
- `--method auto|ensurepip|get-pip` (default: `auto`)
- `--get-pip PATH`: local path to a `get-pip.py` (for offline hosts)
- `--upgrade`: attempt to upgrade pip after bootstrapping

### `pkg pip` (escape hatch)

Run arbitrary `pip` commands on Blender Python (primarily for debugging).

`pkg pip` is the primary mechanism for package management. It forwards `PIP_ARGS...` to a one-shot Blender background run that executes the equivalent of `python -m pip ...` inside Blender’s embedded Python.

**Usage**
```bash
blender-remote-cli pkg pip [OPTIONS] -- PIP_ARGS...
```

Examples:
```bash
blender-remote-cli pkg pip -- list
blender-remote-cli pkg pip -- show numpy
blender-remote-cli pkg pip -- install numpy
blender-remote-cli pkg pip -- install --upgrade requests==2.31.0

# Offline install (wheelhouse path must already exist locally)
blender-remote-cli pkg pip -- install --no-index --find-links ./wheelhouse numpy
```

## User Workflows

### 1) Host has internet

```bash
blender-remote-cli pkg info
blender-remote-cli pkg bootstrap
blender-remote-cli pkg pip -- install numpy
```

### 2) Host is offline (wheelhouse copied in)

```bash
# Create a wheelhouse on another machine (matching Blender Python from `pkg info --json`)
python -m pip download -d ./wheelhouse --only-binary=:all: --platform <PLATFORM_TAG> --python-version <PYXY> --implementation cp numpy requests

# (Out of band) copy ./wheelhouse/* onto the offline host (same local path)

# Install from the wheelhouse
blender-remote-cli pkg pip -- install --no-index --find-links ./wheelhouse numpy requests
```

### 3) Host is offline and missing pip

- User must provide a wheelhouse and (if needed) `get-pip.py` locally:
```bash
blender-remote-cli pkg bootstrap --method get-pip --get-pip ./get-pip.py
blender-remote-cli pkg pip -- install --no-index --find-links ./wheelhouse numpy
```

## Implementation Notes (for later)

### Local probes and paths

All values are derived by invoking Blender locally in background mode with small scripts:
- Blender/Python/platform signature: `<blender> --background --python <probe.py>`
- Site-packages and writability: `<blender> --background --python <probe.py>`
- `pip` availability/version: `<blender> --background --python <pip_probe.py>`

### Reporting and verification

After install, optionally run a lightweight import/version probe:
- `import importlib; importlib.import_module(<name>)`
- Print module `__version__` if available

### Known limitations (communicate in CLI help)

- Wheels must match the host OS/arch and Blender Python major.minor ABI.
- Packages without compatible wheels require building on a matching platform.
- Installing very large packages can take a long time; `pkg pip` output may be truncated in structured results to keep responses bounded.
