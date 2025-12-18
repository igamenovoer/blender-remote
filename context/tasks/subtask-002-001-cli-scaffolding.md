# Subtask 2.1: CLI scaffolding + shared helpers

## Scope

- Add a new `pkg` click group under `blender-remote-cli`.
- Create shared helper utilities for:
  - Resolving the configured Blender executable and invoking it in background mode (`<blender> --background --python <script.py> -- ...`).
  - Running Blender subprocess commands with consistent timeout/error handling (using `cli.timeout_sec`).
  - Extracting/parsing structured results from local probe scripts (JSON printed to stdout).
- Do not implement actual package operations yet (`info/bootstrap/pip/...` are in later subtasks).

## Planned outputs

- `src/blender_remote/cli/commands/pkg.py` (new): `@click.group()` for `pkg` and shared options.
- `src/blender_remote/cli/pkg/` (new package): helpers (Blender background runner, subprocess runner, JSON parsing utilities).
- Basic tests validating the new CLI surface exists and shared helpers behave predictably.

## Testing

### Unit tests (no Blender needed)
- Use `click.testing.CliRunner` to assert:
  - `blender-remote-cli pkg --help` works.
  - `blender-remote-cli pkg info --help` placeholder wiring (even if command is added later) is consistent.
- Add targeted tests for helper utilities:
  - Blender executable resolution precedence (CLI override vs config).
  - JSON parsing helper behavior for success/error outputs.

### Manual smoke test (no Blender needed)
- Run:
  - `blender-remote-cli --help`
  - `blender-remote-cli pkg --help`

## TODOs

- [ ] Job-002-001-001 Create `src/blender_remote/cli/commands/pkg.py` with a `pkg` click group (no subcommands yet or minimal stubs).
- [ ] Job-002-001-002 Register `pkg` in `src/blender_remote/cli/app.py`.
- [ ] Job-002-001-003 Create a `src/blender_remote/cli/pkg/blender_background.py` helper for running `<blender> --background --python <script.py> -- ...`.
- [ ] Job-002-001-004 Create a `src/blender_remote/cli/pkg/subprocess_runner.py` helper for consistent subprocess execution + timeouts.
- [ ] Job-002-001-005 Create `src/blender_remote/cli/pkg/json_output.py` helper that enforces “single JSON object to stdout” behavior when requested.
- [ ] Job-002-001-006 Add unit tests for `pkg` group wiring and helper utilities (mock subprocess).

## Notes

- Keep helper APIs small; later subtasks will build on them.
- Prefer helpers that can be unit-tested without requiring Blender to be running.
