# Subtask 2.2: Implement `pkg info` (+ `--json`)

## Scope

- Implement `blender-remote-cli pkg info` to probe the remote Blender Python environment via `execute_code`.
- Support `--json` mode that prints a single syntax-correct JSON object to stdout (no extra text).
- Ensure probe captures the values needed for the offline wheelhouse workflow (Python version, platform/arch, python executable + args, site-packages, pip availability, online access hint).

## Planned outputs

- `pkg info` click command (likely in `src/blender_remote/cli/commands/pkg.py` or a `pkg_info.py` module under `cli/commands/`).
- A remote probe script template (string builder or embedded script module) that prints JSON deterministically.
- Unit tests validating `--json` mode output discipline.

## Testing

### Unit tests (no Blender needed)
- Mock `connect_and_send_command` to return realistic `execute_code` responses and verify:
  - `pkg info --json` prints JSON only (parseable by `json.loads`).
  - Errors are sent to stderr and a non-zero exit code is used (Click exception).
  - JSON schema stays stable (keys present, types sane).

### Manual integration test (Windows + Blender)
Prereqs (run once):
- `blender-remote-cli init extern/blender-win64/blender-5.0.0-windows-x64/blender.exe`
- `blender-remote-cli install`
- Start Blender MCP in background in a separate terminal (it will block): `blender-remote-cli start --background`

Then in another terminal:
- `blender-remote-cli pkg info`
- `blender-remote-cli pkg info --json | python -c "import json,sys; json.load(sys.stdin); print('OK')"`

## TODOs

- [ ] Job-002-002-001 Implement remote probe script (Python) that prints one JSON object containing platform + Python + pip + site-packages details.
- [ ] Job-002-002-002 Implement `pkg info` human-readable formatting (based on parsed probe JSON).
- [ ] Job-002-002-003 Implement `pkg info --json` mode that prints only JSON to stdout (no extra click.echo noise).
- [ ] Job-002-002-004 Add unit tests for `--json` correctness and error handling (mock transport).
- [ ] Job-002-002-005 Add a brief example snippet to docs draft notes (final docs in subtask 2.7).

## Notes

- Keep the probe fast and robust: no heavyweight imports beyond stdlib + `bpy`.
- Prefer `sys.executable` + `bpy.app.python_args` for pip invocation later.

