# Externals

This directory contains third-party code, binaries, and other large artifacts that are
used during development but are not authored in this repository.

The small metadata files in `extern/` are committed; the populated external trees are
ignored by Git via `extern/.gitignore`.

Managed entries:

- `extern/blender-win64/` - Portable Blender (Windows x64)
  - Upstream: https://download.blender.org/release/
  - Download cache: `tmp/blender-win64/`
  - Purpose: local/dev Blender runtime for scripts, testing, and experimentation

To (re)populate externals, run:

```bash
bash extern/bootstrap.sh
```

On Windows (PowerShell):

```powershell
pwsh -File extern/bootstrap.ps1
```
