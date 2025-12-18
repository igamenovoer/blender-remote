# Subtask 2.2: Implement `pkg info` (+ `--json`)

## Scope

- Implement `blender-remote-cli pkg info` to probe the local Blender Python environment by invoking Blender in background mode (`<blender> --background --python <probe.py>`).
- Support `--json` mode that prints a single syntax-correct JSON object to stdout (no extra text).
- Ensure probe captures the values needed for the offline wheelhouse workflow (Python version, platform/arch, site-packages, pip availability).

## Planned outputs

- `pkg info` click command (likely in `src/blender_remote/cli/commands/pkg.py` or a `pkg_info.py` module under `cli/commands/`).
- A local probe script template (string builder or embedded script module) that prints JSON deterministically, ideally wrapped in sentinel markers so the CLI can extract it even if Blender emits additional logs.
- Unit tests validating `--json` mode output discipline.

## Testing

### Unit tests (no Blender needed)
- Mock subprocess execution to return realistic outputs and verify:
  - `pkg info --json` prints JSON only (parseable by `json.loads`).
  - Errors are sent to stderr and a non-zero exit code is used (Click exception).
  - JSON schema stays stable (keys present, types sane).

### Manual integration test (Windows + Blender)
Prereqs (run once):
- `blender-remote-cli init extern/blender-win64/blender-5.0.0-windows-x64/blender.exe`

Then in another terminal:
- `blender-remote-cli pkg info`
- `blender-remote-cli pkg info --json | python -c "import json,sys; json.load(sys.stdin); print('OK')"`

## TODOs

- [ ] Job-002-002-001 Implement local probe script (Python) that prints one JSON object containing platform + Python + pip + site-packages details.
- [ ] Job-002-002-002 Implement `pkg info` human-readable formatting (based on parsed probe JSON).
- [ ] Job-002-002-003 Implement `pkg info --json` mode that prints only JSON to stdout (no extra click.echo noise).
- [ ] Job-002-002-003a If Blender emits extra output, implement a robust JSON extraction strategy (e.g. sentinel markers).
- [ ] Job-002-002-004 Add unit tests for `--json` correctness and error handling (mock subprocess).
- [ ] Job-002-002-005 Add a brief example snippet to docs draft notes (final docs in subtask 2.7).

## Notes

- Keep the probe fast and robust: no heavyweight imports beyond stdlib.
- Avoid relying on a standalone Blender Python executable; use the configured Blender executable as the runner (`--background --python ...`).
