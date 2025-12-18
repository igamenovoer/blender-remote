# Subtask 2.7: Documentation + end-to-end smoke tests

## Scope

- Update docs to describe the new `pkg` CLI group and workflows.
- Validate an end-to-end offline workflow on Windows using the bundled Blender.
- Ensure documentation calls out common pitfalls (wheel compatibility, permissions, and offline wheelhouse staging).

## Planned outputs

- `docs/manual/cli-tool.md` updated with:
  - `pkg info`, `pkg bootstrap`, `pkg pip`
  - Online vs offline behavior (offline handled via explicit pip flags like `--no-index --find-links`).
  - A complete offline workflow example for Windows (wheelhouse staged locally).
- Optional: small additions to `docs/index.md` linking to the new section.

## Testing

### Docs build test
- Run `pixi run docs-build` (or `pixi run docs-serve`) and ensure MkDocs renders the new CLI docs pages.

### End-to-end smoke test (Windows + Blender)
Prereqs:
- Configure Blender path: `blender-remote-cli init extern/blender-win64/blender-5.0.0-windows-x64/blender.exe`

Workflow (offline-friendly):
1) `blender-remote-cli pkg info --json` (record python version + platform).
2) Build local wheelhouse for Blender Python 3.11 win_amd64:
   - `python -m pip download -d .\\wheelhouse --only-binary=:all: --platform win_amd64 --python-version 311 --implementation cp colorama`
3) Install offline from the local wheelhouse:
   - `blender-remote-cli pkg pip -- install --no-index --find-links .\\wheelhouse colorama`
4) Verify install: `blender-remote-cli pkg pip -- show colorama`

## TODOs

- [ ] Job-002-007-001 Update `docs/manual/cli-tool.md` with `pkg` command reference and examples (online + offline).
- [ ] Job-002-007-002 Add a troubleshooting section (wheel compatibility, permissions, offline wheelhouse staging).
- [ ] Job-002-007-003 Run `pixi run docs-build` to validate docs render.
- [ ] Job-002-007-004 Run the full Windows offline workflow smoke test against `extern/blender-win64/blender-5.0.0-windows-x64`.

## Notes

- Prefer documenting the offline workflow as the reliable baseline (works even when the host has no internet access).
