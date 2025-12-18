# Subtask 2.6: Timeout support for long-running operations

## Scope

- Ensure long-running `pip` operations can run to completion when invoked via Blender background scripts (`<blender> --background --python ...`).
- Keep existing non-`pkg` operations safe and responsive (do not globally increase timeouts without bounds).
- Use the configured CLI timeout (`cli.timeout_sec`) as the default subprocess timeout for `pkg` operations.

## Planned outputs

- CLI changes to use `cli.timeout_sec` for `pkg` subprocess execution without affecting existing commands.
- Tests validating the timeout selection logic (unit) and a manual integration test to prove long runs complete.

## Testing

### Unit tests (no Blender needed)
- Mock subprocess runner and assert:
  - `pkg` subcommands pass `cli.timeout_sec` (or an override) to subprocess execution.
  - Non-`pkg` commands keep existing behavior.

### Manual integration test (Windows + Blender)
Prereqs:
- Configure Blender path: `blender-remote-cli init extern/blender-win64/blender-5.0.0-windows-x64/blender.exe`

Steps:
- Run a deliberate long pip command (or simulate via a long-running Python one-liner if needed):
  - `blender-remote-cli pkg pip -- --help` (quick sanity)
  - `blender-remote-cli pkg pip -- install <SOME_PKG>` (may vary; use offline wheelhouse for reliability)

## TODOs

- [ ] Job-002-006-001 Wire `cli.timeout_sec` into the `pkg` Blender background runner.
- [ ] Job-002-006-002 Add a per-command override option if needed (e.g. `--timeout-sec` on `pkg pip`/`pkg bootstrap`).
- [ ] Job-002-006-003 Add unit tests validating timeout selection logic (mocked subprocess).

## Notes

- Keep outputs bounded: even with longer timeouts, very verbose pip output should not crash the CLI (streaming is preferred).
