# Task: Blender Package Management CLI (`blender-remote-cli pkg ...`)

## HEADER
- **Created**: 2025-12-17
- **Status**: Draft
- **Related design**: `context/design/remote-package-installation.md`
- **Related implementation plan**: `context/plans/plan-remote-package-installation-cli.md`

## 1. Context

We want to manage Python packages for a **local** Blender installation using `blender-remote-cli pkg ...`.

Scope refinement:
- The CLI has direct access to the local Blender executable and its installation directories.
- Package management should run out-of-process by invoking `<blender-executable> --background` with Python scripts and/or manipulating the local filesystem.
- No MCP/RPC (`execute_code`) is required for package installation workflows.

Primary integration target for testing on this repo machine:
- `extern/blender-win64/blender-5.0.0-windows-x64`

## 2. Package management CLI

Scope: Implement the `blender-remote-cli pkg ...` command group (`pkg info`, `pkg bootstrap`, `pkg pip`) as designed in `context/design/remote-package-installation.md`.

Out of scope:
- `pkg install` (use `pkg pip -- install ...`).
- `pkg push` / `pkg purge-cache` (no remote/local file management).

Planned outputs:
- New click command group `pkg` registered under `blender-remote-cli`.
- Local probe + pip execution run via `<blender-executable> --background` scripts (no direct Blender Python executable usage).
- Offline workflow support via local wheelhouse: user stages wheels locally, then runs `pkg pip -- install --no-index --find-links <PATH> ...`.
- Documentation updates for the new commands and workflows.

Milestones (subtasks):

### 2.1 CLI scaffolding + shared helpers

Goal: Wire the `pkg` command group into the CLI and create shared helpers for resolving the configured Blender executable and running `<blender> --background --python <script.py> -- ...` with consistent timeouts and error reporting.

- Subtask spec: `context/tasks/subtask-002-001-cli-scaffolding.md`

### 2.2 `pkg info` (+ `--json`)

Goal: Implement a local Blender Python environment probe (via Blender background scripts) and provide both human-readable and strict JSON output modes.

- Subtask spec: `context/tasks/subtask-002-002-pkg-info-json.md`

### 2.3 `pkg bootstrap` (ensure pip exists)

Goal: Implement `pip` bootstrapping with `ensurepip` (preferred) and a local `get-pip.py` fallback.

- Subtask spec: `context/tasks/subtask-002-003-pkg-bootstrap.md`

### 2.4 `pkg pip` (escape hatch)

Goal: Implement `pkg pip -- ...` passthrough to run arbitrary `pip` commands via Blender background scripts.

- Subtask spec: `context/tasks/subtask-002-004-pkg-pip-and-install.md`

### 2.5 Removed: `pkg push` + `pkg purge-cache`

These commands are removed from scope; file staging/cleanup is handled out-of-band by the user.

### 2.6 Timeout support for long-running operations

Goal: Ensure `pip` operations can run longer than short default timeouts by using the configured CLI timeout (`cli.timeout_sec`) for subprocess execution.

- Subtask spec: `context/tasks/subtask-002-006-timeout-support.md`

### 2.7 Documentation + end-to-end smoke tests

Goal: Update docs for the new `pkg` CLI and validate an end-to-end workflow on Windows using the bundled Blender.

- Subtask spec: `context/tasks/subtask-002-007-docs-and-smoke-tests.md`

TODOs (milestone-level jobs):
- [ ] Job-002-001 Complete subtask 2.1 (CLI scaffolding + shared helpers)
- [ ] Job-002-002 Complete subtask 2.2 (`pkg info` + `--json`)
- [ ] Job-002-003 Complete subtask 2.3 (`pkg bootstrap`)
- [ ] Job-002-004 Complete subtask 2.4 (`pkg pip`)
- [ ] Job-002-006 Complete subtask 2.6 (timeouts)
- [ ] Job-002-007 Complete subtask 2.7 (docs + e2e smoke tests)
