# Subtask 2.4: Implement `pkg pip`

## Scope

- Implement a “pip runner” that executes pip via Blender background mode:
  - `blender.exe --background --python <pip_runner.py> -- <PIP_ARGS...>`
  - the runner uses `runpy.run_module("pip", run_name="__main__")` to emulate `python -m pip ...` inside Blender’s embedded Python.
  - return structured results (return code, captured stdout/stderr, duration).
- Implement `blender-remote-cli pkg pip [OPTIONS] -- PIP_ARGS...` as the general escape hatch.

## Planned outputs

- Pip runner used by `pkg pip`.
- `pkg pip` click command implementation.
- Unit tests for argument handling and command construction.

## Testing

### Unit tests (no Blender needed)
- Use `CliRunner` and mock the subprocess runner to verify:
  - `pkg pip -- --version` passes `["--version"]` to the runner.
  - `pkg pip -- install --no-index --find-links ./wheelhouse numpy` forwards args verbatim.

### Manual integration test (Windows + Blender)
Prereqs:
- Configure Blender path as in subtask 2.2.

Steps (network-independent):
- `blender-remote-cli pkg pip -- --version`
- `blender-remote-cli pkg pip -- list`

Optional steps:
- Online: `blender-remote-cli pkg pip -- install colorama`
- Offline: `blender-remote-cli pkg pip -- install --no-index --find-links ./wheelhouse colorama`

## TODOs

- [ ] Job-002-004-001 Implement pip runner (invoke Blender background mode and run pip module in-process).
- [ ] Job-002-004-002 Implement `pkg pip` command and `--` passthrough semantics.
- [ ] Job-002-004-003 Add unit tests for argument parsing + pip arg forwarding (mock subprocess).

## Notes

- Ensure `pkg info --json` and `pkg pip` can be used to debug most failures.
- Keep output bounded: very verbose pip output may need truncation when returning structured results.
