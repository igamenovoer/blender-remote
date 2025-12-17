# Subtask 2.1: CLI scaffolding + shared helpers

## Scope

- Add a new `pkg` click group under `blender-remote-cli`.
- Create shared helper utilities for:
  - Resolving port (`--port` → config → default).
  - Sending `execute_code` with optional base64 encoding.
  - Extracting/parsing structured results from the existing `execute_code` response shape.
- Do not implement actual package operations yet (`info/bootstrap/install/push/...` are in later subtasks).

## Planned outputs

- `src/blender_remote/cli/commands/pkg.py` (new): `@click.group()` for `pkg` and shared options.
- `src/blender_remote/cli/pkg/` (new package): helpers (port resolution, remote exec wrapper, JSON parsing utilities).
- Basic tests validating the new CLI surface exists and shared helpers behave predictably.

## Testing

### Unit tests (no Blender needed)
- Use `click.testing.CliRunner` to assert:
  - `blender-remote-cli pkg --help` works.
  - `blender-remote-cli pkg info --help` placeholder wiring (even if command is added later) is consistent.
- Add targeted tests for helper utilities:
  - Port resolution precedence.
  - JSON parsing helper behavior for success/error responses.

### Manual smoke test (no Blender needed)
- Run:
  - `blender-remote-cli --help`
  - `blender-remote-cli pkg --help`

## TODOs

- [ ] Job-002-001-001 Create `src/blender_remote/cli/commands/pkg.py` with a `pkg` click group (no subcommands yet or minimal stubs).
- [ ] Job-002-001-002 Register `pkg` in `src/blender_remote/cli/app.py`.
- [ ] Job-002-001-003 Create `src/blender_remote/cli/pkg/remote_exec.py` helper wrapping `connect_and_send_command("execute_code", ...)` with base64 support.
- [ ] Job-002-001-004 Create `src/blender_remote/cli/pkg/ports.py` helper for resolving the MCP port consistently across commands.
- [ ] Job-002-001-005 Create `src/blender_remote/cli/pkg/json_output.py` helper that enforces “single JSON object to stdout” behavior when requested.
- [ ] Job-002-001-006 Add unit tests for `pkg` group wiring and helper utilities (mock `connect_and_send_command`).

## Notes

- Keep helper APIs small; later subtasks will build on them.
- Prefer helpers that can be unit-tested without requiring Blender to be running.

