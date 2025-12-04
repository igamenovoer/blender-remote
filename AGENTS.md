# Repository Guidelines

## Project Structure & Module Organization
- Core library: `src/blender_remote/` (CLI, MCP server, client API, addon).
- Tests: `tests/` for automated pytest-based suites; `tmp/` for temporary or manual experiment files only.
- Documentation: `docs/` with MkDocs configuration in `mkdocs.yml`.
- Utility scripts and examples: `scripts/` and `examples/`; avoid importing from `tmp/` or build artifacts.

## Build, Test, and Development Commands
- Use `pixi` for development: `pixi install` then run tasks with `pixi run <task>`.
- Format and lint: `pixi run format` (Black) and `pixi run lint` (Ruff) before opening a PR.
- Type checking: `pixi run type-check` (mypy on `src/`).
- Tests: `pixi run test` for the main suite, `pixi run test-cov` for coverage.
- Docs: `pixi run docs-serve` (local preview) and `pixi run docs-build` (build site).

## Coding Style & Naming Conventions
- Python only: 4-space indentation, max line length 88 (Black/Ruff config).
- Names: modules and functions in `snake_case`, classes in `CamelCase`, constants in `UPPER_SNAKE_CASE`.
- Keep public APIs in `blender_remote` stable; prefer small, composable helpers over large functions.
- Run `pixi run format` and `pixi run lint` and fix all reported issues before committing.

## Testing Guidelines
- Place unit tests in `tests/` and mirror the package structure where practical (e.g., `tests/test_client.py` for `client.py`).
- Follow pytest naming: files `test_*.py` or `*_test.py`, functions `test_*`.
- New features and bug fixes should include or update tests; aim to keep coverage from regressing (use `pixi run test-cov` when changing core behavior).

## Commit & Pull Request Guidelines
- Prefer Conventional Commit style, e.g., `feat(cli): add batch export`, `fix: handle missing Blender path`, `docs: update MCP usage`.
- Keep commits focused and logically grouped; avoid mixing formatting-only changes with behavior changes.
- PRs should include: a clear summary, rationale, key tests run (with commands, e.g., `pixi run test`), and links to related issues (`Fixes #123`).
- For changes affecting cross-platform behavior or Blender startup, describe how you tested on at least one platform and include relevant logs or notes.

## Security & Configuration Notes
- Do not commit secrets, API keys, or machine-specific configuration; use environment variables or local config files ignored by Git.
- Treat `tmp/` as ephemeral; nothing there is considered stable API or part of releases.

