# Subtask 2.6: Timeout support for long-running operations

## Scope

- Address the current `BLD_Remote_MCP` command execution timeout (30s) so that:
  - `pip` installs can run longer.
  - large wheel uploads (many chunks) remain reliable.
- Keep existing non-`pkg` operations safe and responsive (do not globally increase timeouts without bounds).
- Add a CLI-side timeout strategy so socket receive can wait long enough for long-running operations.

## Planned outputs

- Addon changes in `src/blender_remote/addon/bld_remote_mcp/__init__.py` to support longer-running requests (ideally per-command override).
- CLI changes to use longer socket timeouts for `pkg` subcommands without affecting existing commands.
- Tests validating the timeout override wiring (unit) and a manual integration test to prove >30s runs.

## Testing

### Unit tests (no Blender needed)
- Mock remote exec wrapper and assert:
  - `pkg` subcommands pass an increased timeout to transport (or select a larger default).
  - Non-`pkg` commands keep current timeouts.

### Manual integration test (Windows + Blender)
Prereqs:
- Re-install addon after code changes: `blender-remote-cli install`
- Start Blender MCP service: `blender-remote-cli start --background` (separate terminal; blocks).

Steps:
- Run a deliberate long remote script:
  - `blender-remote-cli execute --code \"import time; time.sleep(45); print('done')\"`
  - Expect: success (this should fail before this subtask is complete).
- Run a pip command that can take time (example):
  - `blender-remote-cli pkg pip -- --help` (quick sanity)
  - `blender-remote-cli pkg install ...` (may vary; offline recommended).

## TODOs

- [ ] Job-002-006-001 Identify where the 30s timeout is enforced in the addon (`COMMAND_EXECUTION_TIMEOUT_SECONDS`) and decide on an override mechanism.
- [ ] Job-002-006-002 Implement per-command timeout override support (e.g., allow `execute_code` to accept a `timeout_seconds` param, defaulting to existing config).
- [ ] Job-002-006-003 Update CLI `pkg` subcommands to request a longer remote timeout for pip/upload operations.
- [ ] Job-002-006-004 Update CLI transport timeout behavior for `pkg` commands so socket receive doesn’t fail early.
- [ ] Job-002-006-005 Add unit tests validating timeout selection logic (mocked).

## Notes

- Keep outputs bounded: even with longer timeouts, responses must stay under the socket max response size.

