# Subtask 2.5: Implement `pkg push` and `pkg purge-cache`

## Scope

- Implement `blender-remote-cli pkg push` to upload `.whl` files from the controller into a remote wheelhouse directory.
- Upload must be chunked (default 5 MiB pre-base64), safe against path traversal, and resilient to partial failures.
- Implement `blender-remote-cli pkg purge-cache` to remove all files/directories inside the remote wheelhouse directory (does not uninstall packages).

## Planned outputs

- `pkg push` click command implementation (wheel discovery, chunk splitting, remote write protocol).
- `pkg purge-cache` click command implementation (confirmation + remote deletion).
- Helper utilities:
  - Wheel discovery from directories and `.whl` paths.
  - Safe filename validation.
  - Chunked base64 encoding and remote append/finalize logic.
- Unit tests for helpers and CLI plumbing.

## Testing

### Unit tests (no Blender needed)
- Validate:
  - Directory discovery finds `.whl` files deterministically.
  - Unsafe filenames (path separators, `..`) are rejected.
  - Chunk splitting boundaries and base64 encoding round-trips (local-only).
  - `pkg purge-cache` requires `--yes` or interactive confirmation.

### Manual integration test (Windows + Blender, offline workflow)
Prereqs:
- Install + start Blender MCP service as in subtask 2.2 (run `start --background` in a separate terminal).

Steps:
1) Build a local wheelhouse for Blender’s Python (3.11 win_amd64):
   - `python -m pip download -d .\\wheelhouse --only-binary=:all: --platform win_amd64 --python-version 311 --implementation cp colorama`
2) Upload wheels:
   - `blender-remote-cli pkg push .\\wheelhouse --remote-wheelhouse C:/tmp/blender-remote/wheels`
3) Install offline:
   - `blender-remote-cli pkg install colorama --remote-wheelhouse C:/tmp/blender-remote/wheels`
4) Verify import:
   - `blender-remote-cli execute --code \"import colorama; print(colorama.__version__)\"`
5) Purge cache:
   - `blender-remote-cli pkg purge-cache --remote-wheelhouse C:/tmp/blender-remote/wheels --yes`
   - Optionally verify directory is empty via `execute`.

## TODOs

- [ ] Job-002-005-001 Implement wheel discovery for `pkg push` (accept directories and `.whl` paths).
- [ ] Job-002-005-002 Implement safe filename validation to prevent remote path traversal.
- [ ] Job-002-005-003 Implement remote write protocol:
  - ensure remote wheelhouse directory exists
  - upload bytes in base64 chunks and append on remote
  - finalize file (atomic rename if possible)
- [ ] Job-002-005-004 Implement `pkg push --chunk-size` and choose a safe default (5 MiB pre-base64).
- [ ] Job-002-005-005 Implement `pkg purge-cache` remote deletion and `--yes` confirmation bypass.
- [ ] Job-002-005-006 Add unit tests for discovery, validation, and chunk logic (mock remote exec).

## Notes

- This subtask depends on the remote exec helper (2.1) and pip runner (2.4) for full offline workflow validation.

