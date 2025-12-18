# Subtask 2.3: Implement `pkg bootstrap`

## Scope

- Implement `blender-remote-cli pkg bootstrap` to ensure `pip` exists and is usable for Blender Python (local install).
- Support `--method auto|ensurepip|get-pip`, `--get-pip PATH`, and `--upgrade` as described in `context/design/remote-package-installation.md`.
- Keep behavior safe and explicit for offline hosts (`--get-pip` may be required).

## Planned outputs

- `pkg bootstrap` click command implementation.
- Bootstrap logic that:
  - checks pip usability (pip `--version` equivalent) via a Blender background run,
  - runs ensurepip via a Blender background run,
  - falls back to executing a user-provided local `get-pip.py`.
- Unit tests covering CLI decision logic and error reporting.

## Testing

### Unit tests (no Blender needed)
- Mock the subprocess runner to simulate:
  - `pip` already present → no-op success.
  - `pip` missing + ensurepip works → success.
  - ensurepip fails and `--get-pip` not provided (offline host) → user-facing error.
  - `--method get-pip --get-pip <path>` triggers local script execution flow.

### Manual integration test (Windows + Blender)
Prereqs:
- Configure Blender path as in subtask 2.2.

Steps:
- `blender-remote-cli pkg bootstrap` (expect: reports pip already available on Blender 5.0.0, or successfully bootstraps).
- `blender-remote-cli pkg pip -- --version` (sanity check that pip is runnable).

## TODOs

- [ ] Job-002-003-001 Implement “pip present?” check using the Blender background pip runner primitive (pip `--version` equivalent).
- [ ] Job-002-003-002 Implement ensurepip path (via Blender background runner) and report outcome in structured JSON.
- [ ] Job-002-003-003 Implement get-pip fallback:
  - require `--get-pip PATH` for offline hosts
  - execute it via a Blender background run
- [ ] Job-002-003-004 Implement `--upgrade` post-step (best-effort; expect failures on offline hosts).
- [ ] Job-002-003-005 Add unit tests for the decision tree and user-facing messages.

## Notes

- Keep bootstrap scripts idempotent where possible.
- If the host is offline, `--upgrade` should fail clearly and suggest an offline wheelhouse workflow.
