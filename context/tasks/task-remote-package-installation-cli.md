# Task: Remote Package Installation CLI (`blender-remote-cli pkg ...`)

## HEADER
- **Created**: 2025-12-17
- **Status**: Draft
- **Related design**: `context/design/remote-package-installation.md`
- **Related implementation plan**: `context/plans/plan-remote-package-installation-cli.md`

## 1. Context

We want to add remote PyPI package installation into Blender’s embedded Python via the existing `execute_code` RPC, supporting both online and offline remote Blender hosts.

Primary integration target for testing on this repo machine:
- `extern/blender-win64/blender-5.0.0-windows-x64`

## 2. Remote package installation CLI

Scope: Implement the `blender-remote-cli pkg ...` command group (`pkg info`, `pkg bootstrap`, `pkg install`, `pkg pip`, `pkg push`, `pkg purge-cache`) as designed in `context/design/remote-package-installation.md`.

Planned outputs:
- New click command group `pkg` registered under `blender-remote-cli`.
- Remote probe + pip execution scripts run via `execute_code`.
- Offline workflow support via remote wheelhouse cache: `pkg push` → `pkg install --remote-wheelhouse ...`.
- Documentation updates for the new commands and workflows.

Milestones (subtasks):

### 2.1 CLI scaffolding + shared helpers

Goal: Wire the `pkg` command group into the CLI and create shared helpers for port resolution, execute_code invocation, base64 handling, and parsing structured stdout.

- Subtask spec: `context/tasks/subtask-002-001-cli-scaffolding.md`

### 2.2 `pkg info` (+ `--json`)

Goal: Implement a remote environment probe and provide both human-readable and strict JSON output modes.

- Subtask spec: `context/tasks/subtask-002-002-pkg-info-json.md`

### 2.3 `pkg bootstrap` (ensure pip exists remotely)

Goal: Implement `pip` bootstrapping with `ensurepip` (preferred) and `get-pip.py` transfer fallback.

- Subtask spec: `context/tasks/subtask-002-003-pkg-bootstrap.md`

### 2.4 `pkg pip` (escape hatch) and `pkg install` (wrapper)

Goal: Implement the remote pip runner, the generic `pkg pip -- ...` passthrough, and the simplified `pkg install` wrapper (online default; offline when `--remote-wheelhouse` is provided).

- Subtask spec: `context/tasks/subtask-002-004-pkg-pip-and-install.md`

### 2.5 `pkg push` (chunked wheel upload) + `pkg purge-cache`

Goal: Implement chunked upload of `.whl` files into a remote wheelhouse cache and provide a purge-cache command to delete remote cached wheels.

- Subtask spec: `context/tasks/subtask-002-005-pkg-push-and-purge-cache.md`

### 2.6 Timeout support for long-running operations

Goal: Ensure `pip` operations and large uploads can run longer than the current addon’s 30s command timeout, without breaking existing commands.

- Subtask spec: `context/tasks/subtask-002-006-timeout-support.md`

### 2.7 Documentation + end-to-end smoke tests

Goal: Update docs for the new `pkg` CLI and validate an end-to-end workflow on Windows using the bundled Blender.

- Subtask spec: `context/tasks/subtask-002-007-docs-and-smoke-tests.md`

TODOs (milestone-level jobs):
- [ ] Job-002-001 Complete subtask 2.1 (CLI scaffolding + shared helpers)
- [ ] Job-002-002 Complete subtask 2.2 (`pkg info` + `--json`)
- [ ] Job-002-003 Complete subtask 2.3 (`pkg bootstrap`)
- [ ] Job-002-004 Complete subtask 2.4 (`pkg pip` + `pkg install`)
- [ ] Job-002-005 Complete subtask 2.5 (`pkg push` + `pkg purge-cache`)
- [ ] Job-002-006 Complete subtask 2.6 (timeouts)
- [ ] Job-002-007 Complete subtask 2.7 (docs + e2e smoke tests)

