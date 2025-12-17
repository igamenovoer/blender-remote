# Subtask 2.3: Implement `pkg bootstrap`

## Scope

- Implement `blender-remote-cli pkg bootstrap` to ensure `pip` exists and is usable in the remote Blender Python.
- Support `--method auto|ensurepip|get-pip`, `--get-pip PATH`, and `--upgrade` as described in `context/design/remote-package-installation.md`.
- Keep behavior safe and explicit for offline remotes (controller may need to provide `--get-pip`).

## Planned outputs

- `pkg bootstrap` click command implementation.
- Remote bootstrap script(s) that:
  - checks `python -m pip --version`,
  - runs `python -m ensurepip --upgrade`,
  - falls back to executing transferred `get-pip.py`.
- Unit tests covering CLI decision logic and error reporting.

## Testing

### Unit tests (no Blender needed)
- Mock the remote runner to simulate:
  - `pip` already present → no-op success.
  - `pip` missing + ensurepip works → success.
  - ensurepip fails and `--get-pip` not provided (controller offline) → user-facing error.
  - `--method get-pip --get-pip <path>` triggers file transfer flow (mocked) and execution flow.

### Manual integration test (Windows + Blender)
Prereqs:
- Install + start Blender MCP service as in subtask 2.2 (use `blender-remote-cli start --background` in a separate terminal).

Steps:
- `blender-remote-cli pkg bootstrap` (expect: reports pip already available on Blender 5.0.0, or successfully bootstraps).
- `blender-remote-cli pkg pip -- --version` (sanity check that pip is runnable remotely).

## TODOs

- [ ] Job-002-003-001 Implement remote “pip present?” check using the pip runner primitive (`python -m pip --version`).
- [ ] Job-002-003-002 Implement ensurepip path (`python -m ensurepip --upgrade`) and report outcome in structured JSON.
- [ ] Job-002-003-003 Implement get-pip fallback:
  - controller downloads `get-pip.py` when possible, otherwise requires `--get-pip PATH`
  - transfer to remote and execute it via remote python
- [ ] Job-002-003-004 Implement `--upgrade` post-step (best-effort; expect failures on offline remotes).
- [ ] Job-002-003-005 Add unit tests for the decision tree and user-facing messages.

## Notes

- Keep bootstrap scripts idempotent where possible.
- If remote `bpy.app.online_access` is false, online bootstrap should fail clearly and suggest offline `--get-pip`.

