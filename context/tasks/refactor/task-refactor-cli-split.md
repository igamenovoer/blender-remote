# Refactor Plan: Split `src/blender_remote/cli.py` into Smaller Modules

## What to Refactor

- Refactor the monolithic CLI implementation in `src/blender_remote/cli.py` into a small package with focused modules (proposed: `src/blender_remote/cli/`).
- Extract and group responsibilities currently mixed together:
  - Config management (`BlenderRemoteConfig`, config paths, OmegaConf I/O)
  - Blender discovery and installation probing (Windows registry, macOS Spotlight, background detection script)
  - Addon packaging + Blender-driven addon installation scripts (duplicated code in `install` + `debug install`)
  - TCP transport helpers (`connect_and_send_command`)
  - CLI command wiring (Click groups/commands)
  - Large embedded Python templates (`KEEPALIVE_SCRIPT`, debug startup templates)

## Why Refactor

- `src/blender_remote/cli.py` currently mixes multiple concerns, making it difficult to:
  - safely change or extend one command without touching unrelated code
  - reuse shared logic (e.g., addon installation script generation is duplicated)
  - test individual pieces (transport, config, detection) in isolation
  - keep cross-module dependencies clear (e.g., `src/blender_remote/mcp_server.py` imports `BlenderRemoteConfig`)
- Splitting improves readability and lowers risk of regressions when adding new CLI features.

## How to Refactor

### 1) Choose the target module layout

Convert `blender_remote.cli` from a single file to a package, keeping the public entrypoint stable (`blender-remote-cli = blender_remote.cli:cli`).

Proposed structure:

```
src/blender_remote/cli/
  __init__.py            # exports: cli, BlenderRemoteConfig (compat)
  app.py                 # click group + command registration
  constants.py           # CONFIG_DIR/CONFIG_FILE + shared constants
  config.py              # BlenderRemoteConfig implementation
  detection.py           # find_blender_executable_* + detect_blender_info
  addon.py               # addon zip discovery + install-script builder
  transport.py           # connect_and_send_command (TCP JSON)
  scripts.py             # KEEPALIVE_SCRIPT + other embedded templates
  commands/
    init.py
    install.py
    config_cmd.py
    export.py
    start.py
    execute.py
    status.py
    debug.py
```

Notes:
- Avoid creating `src/cli/...` as a top-level package because packaging currently includes only `blender_remote*` (`pyproject.toml`), so top-level `cli` would not ship without additional packaging changes.
- Keep backwards compatibility for imports used elsewhere (notably `src/blender_remote/mcp_server.py`).

### 2) Establish a compatibility surface (no behavior changes)

- Ensure `blender_remote.cli:cli` continues to resolve.
- Re-export `BlenderRemoteConfig` from `src/blender_remote/cli/__init__.py` so the existing import in `src/blender_remote/mcp_server.py` remains valid:
  - `from blender_remote.cli import BlenderRemoteConfig`
- Keep command names, options, defaults, and output formatting unchanged.

### 3) Extract pure helpers first

- Move these into new modules with minimal edits:
  - `BlenderRemoteConfig` -> `cli/config.py`
  - Config file locations -> `cli/constants.py`
  - Blender detection helpers -> `cli/detection.py`
  - TCP helper -> `cli/transport.py`

### 4) Deduplicate addon installation script generation

Create a shared helper that builds the Blender-side Python script (used by both `install` and `debug install`):

```python
# src/blender_remote/cli/addon.py
def build_addon_install_script(addon_zip_path: str, addon_module_name: str) -> str:
    ...
```

Then both commands call the shared function and run Blender with `--background --python <temp_script>`.

### 5) Split commands into `cli/commands/*`

Prefer explicit command registration to avoid circular imports:

**Before (current pattern):**
```python
# src/blender_remote/cli.py
@click.group()
def cli(): ...

@cli.command()
def init(...): ...
```

**After (explicit registration):**
```python
# src/blender_remote/cli/app.py
@click.group()
def cli(): ...

from .commands.init import init
cli.add_command(init)
```

```python
# src/blender_remote/cli/commands/init.py
@click.command()
def init(...): ...
```

Do the same for grouped commands (`config`, `debug`) by defining them as `@click.group()` in their module and adding them via `cli.add_command(config)`.

### 6) Isolate large embedded templates

- Move `KEEPALIVE_SCRIPT` and debug startup templates to `cli/scripts.py` (or, optionally, to package data files if we want to keep templates as real `.py` files).
- Keep the `export keep-alive.py` command behavior the same, but source the content from the new module.

### 7) Run checks and validate behavior

- Static checks:
  - `pixi run format`
  - `pixi run lint`
  - `pixi run type-check`
- Tests:
  - `pixi run test`
- Manual smoke checks (no Blender required):
  - `blender-remote-cli --help`
  - `blender-remote-cli config --help`
  - `blender-remote-cli debug --help`

## Impact Analysis

- **Expected functional impact:** none (refactor-only).
- **Key risks:**
  - Import path changes when converting `cli.py` into a package could break `blender-remote-cli` entrypoint or internal imports.
  - Circular imports if command modules import the click group incorrectly.
  - `src/blender_remote/mcp_server.py` depends on `BlenderRemoteConfig` being importable from `blender_remote.cli`.
- **Mitigations:**
  - Keep the entrypoint string unchanged and ensure `cli` exists at `blender_remote/cli/__init__.py`.
  - Use explicit `cli.add_command(...)` registration rather than decorator-based `@cli.command()` across modules.
  - Re-export `BlenderRemoteConfig` from `blender_remote.cli` for compatibility.
  - Run `pixi run type-check` to catch missing re-exports and import errors early.

## Expected Outcome

- `blender_remote.cli` becomes a maintainable package with clear separation of concerns.
- Shared logic (addon installation scripts, detection, transport) becomes reusable and testable.
- Eliminates duplication (notably the addon install script logic used by both install paths).
- Future CLI extensions become smaller, localized changes (new command modules + registration).

## References

- Code:
  - `src/blender_remote/cli.py`
  - `src/blender_remote/mcp_server.py`
  - `pyproject.toml` (`[project.scripts]` entrypoints and packaging include rules)
- Docs:
  - `docs/manual/cli-tool.md`
- Planning guidelines:
  - `magic-context/instructions/planning/make-refactor-plan.md`
- Third-party libraries (Context7):
  - Click: `/pallets/click`
  - OmegaConf: `/omry/omegaconf`
  - platformdirs: `/tox-dev/platformdirs`

