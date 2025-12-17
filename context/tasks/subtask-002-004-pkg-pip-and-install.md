# Subtask 2.4: Implement `pkg pip` and `pkg install`

## Scope

- Implement a remote “pip runner” that executes pip via Blender’s Python:
  - `subprocess.run([sys.executable, *bpy.app.python_args, "-m", "pip", ...])`
  - return structured JSON: return code, stdout/stderr (truncated), duration.
- Implement `blender-remote-cli pkg pip [OPTIONS] -- PIP_ARGS...` as the general escape hatch.
- Implement `blender-remote-cli pkg install [OPTIONS] PACKAGE_SPEC...` as a convenience wrapper:
  - Online default if `--remote-wheelhouse` is omitted.
  - Offline if `--remote-wheelhouse PATH` is present: imply `--no-index --find-links PATH`.
- Enforce the “simple package specs” rule for `pkg install` (complex cases go through `pkg pip`).

## Planned outputs

- Remote pip runner script template used by both `pkg pip` and `pkg install`.
- `pkg pip` click command implementation.
- `pkg install` click command implementation.
- Unit tests for argument handling and command construction.

## Testing

### Unit tests (no Blender needed)
- Use `CliRunner` and mock the remote execution wrapper to verify:
  - `pkg pip -- --version` passes `["--version"]` to the runner.
  - `pkg install numpy<2` constructs the correct remote pip args.
  - `pkg install --remote-wheelhouse X numpy` adds `--no-index --find-links X`.
  - Invalid `pkg install` specs (e.g., `-r req.txt`, URLs, local paths) are rejected with a clear error directing users to `pkg pip`.

### Manual integration test (Windows + Blender)
Prereqs:
- Install + start Blender MCP service as in subtask 2.2.

Steps (network-independent):
- `blender-remote-cli pkg pip -- --version`
- `blender-remote-cli pkg pip -- list`

Optional steps (may fail if Blender disallows network via `bpy.app.online_access`):
- `blender-remote-cli pkg install colorama` (expect success if remote has internet; otherwise expect a clear error suggesting offline workflow).

## TODOs

- [ ] Job-002-004-001 Implement remote pip runner code generation (subprocess invocation via `sys.executable` + `bpy.app.python_args`).
- [ ] Job-002-004-002 Implement `pkg pip` command and `--` passthrough semantics.
- [ ] Job-002-004-003 Implement `pkg install` wrapper with `--upgrade`, `--force-reinstall`, `--no-deps`, and `--remote-wheelhouse`.
- [ ] Job-002-004-004 Implement “simple package spec” validation for `pkg install` (direct complex users to `pkg pip`).
- [ ] Job-002-004-005 Add unit tests for argument parsing + pip arg construction (mock transport).

## Notes

- Ensure `pkg info --json` and `pkg pip` can be used to debug most failures.
- Truncate pip output in structured JSON to avoid hitting the 10MB socket response cap.

