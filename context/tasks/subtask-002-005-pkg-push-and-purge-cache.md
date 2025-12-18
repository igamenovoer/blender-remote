# Subtask 2.5: Removed (`pkg push` / `pkg purge-cache`)

## Scope

This subtask is intentionally removed from scope.

Rationale:
- `blender-remote-cli` manages a local Blender installation and has direct filesystem access.
- We do not manage user files (no upload, no cache directory lifecycle, no deletion commands).
- Users stage wheelhouses/files via any out-of-band method and then use `pkg pip` with local paths.

## Planned outputs

- None.

## Testing

No tests.

## TODOs

- None.

## Notes

- See `context/design/remote-package-installation.md` for the updated scope and offline workflow.
