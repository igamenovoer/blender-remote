# Subtask 2.7: Documentation + end-to-end smoke tests

## Scope

- Update docs to describe the new `pkg` CLI group and workflows.
- Validate an end-to-end offline workflow on Windows using the bundled Blender.
- Ensure documentation calls out common pitfalls (offline remote, `bpy.app.online_access`, and background process blocking).

## Planned outputs

- `docs/manual/cli-tool.md` updated with:
  - `pkg info`, `pkg bootstrap`, `pkg install`, `pkg pip`, `pkg push`, `pkg purge-cache`
  - Online vs offline behavior (offline implied by `--remote-wheelhouse`).
  - A complete offline workflow example for Windows.
- Optional: small additions to `docs/index.md` linking to the new section.

## Testing

### Docs build test
- Run `pixi run docs-build` (or `pixi run docs-serve`) and ensure MkDocs renders the new CLI docs pages.

### End-to-end smoke test (Windows + Blender)
Prereqs:
- Configure Blender path: `blender-remote-cli init extern/blender-win64/blender-5.0.0-windows-x64/blender.exe`
- Install addon into that Blender: `blender-remote-cli install`
- Start Blender MCP service in background in a separate terminal (it blocks): `blender-remote-cli start --background`

Workflow (offline-friendly):
1) `blender-remote-cli pkg info --json` (record python version + platform).
2) Build local wheelhouse for Blender Python 3.11 win_amd64:
   - `python -m pip download -d .\\wheelhouse --only-binary=:all: --platform win_amd64 --python-version 311 --implementation cp colorama`
3) `blender-remote-cli pkg push .\\wheelhouse --remote-wheelhouse C:/tmp/blender-remote/wheels`
4) `blender-remote-cli pkg install colorama --remote-wheelhouse C:/tmp/blender-remote/wheels`
5) Verify import: `blender-remote-cli execute --code \"import colorama; print(colorama.__version__)\"`
6) Purge cache: `blender-remote-cli pkg purge-cache --remote-wheelhouse C:/tmp/blender-remote/wheels --yes`

Process control note:
- Do not run `blender.exe --background` directly for these tests unless you provide a keep-alive script; `blender-remote-cli start --background` already does this but will block the launching terminal.

## TODOs

- [ ] Job-002-007-001 Update `docs/manual/cli-tool.md` with `pkg` command reference and examples (online + offline).
- [ ] Job-002-007-002 Add a troubleshooting section (offline remote, wheel compatibility, permissions, background blocking).
- [ ] Job-002-007-003 Run `pixi run docs-build` to validate docs render.
- [ ] Job-002-007-004 Run the full Windows offline workflow smoke test against `extern/blender-win64/blender-5.0.0-windows-x64`.

## Notes

- Prefer documenting the offline workflow as the reliable baseline (Blender may default to `bpy.app.online_access == False`).

