# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

blender-remote is a Python project that enables remote control of Blender through:
- Blender add-ons that run services inside Blender to receive and execute commands
- A Python package for remote control from outside the Blender environment
- MCP (Model Context Protocol) server integration for communication
- CLI tools for command-line interaction

The project is designed to be published on PyPI as `pip install blender-remote`.

## Project Structure

```
blender-remote/
├── blender_addon/      # Blender add-ons (plugins) that run services inside Blender
├── src/                # Source code (src layout)
│   └── blender_remote/ # Python package for remote control from outside Blender
├── scripts/            # CLI tools for command-line interaction
├── tests/              # Test suite
├── docs/               # Documentation source
├── context/            # AI assistant workspace
│   ├── design/         # API and technical design docs
│   ├── plans/          # Implementation roadmaps
│   ├── hints/          # Programming guides and tutorials
│   ├── summaries/      # Project knowledge base
│   ├── tasks/          # Human-defined task requests
│   ├── logs/           # Development history logs
│   ├── refcode/        # Reference implementations
│   └── tools/          # Custom development utilities
├── pyproject.toml      # Python package configuration
└── README.md           # Project documentation
```

## Development Environment

- Python environment is managed by **pixi** (see pixi.toml)
- The project targets publication to PyPI
- Development commands:
  - `pixi run test` - Run tests
  - `pixi run lint` - Run linting
  - `pixi run format` - Format code
  - `pixi run build` - Build package

## Architecture Overview

1. **Blender Add-ons** (`blender_addon/`): Multiple add-ons that create non-stop services inside Blender. These services listen for commands and execute them using Blender's Python API.

2. **Remote Control Library** (`src/blender_remote/`): Python package used outside of Blender to connect to the add-ons and control Blender. Usage pattern: `import blender_remote.xxxx`

3. **MCP Server Integration**: Provides the communication protocol between the remote control library and Blender add-ons.

4. **CLI Tools** (`scripts/`): Command-line interface tools for remote Blender control operations.

## Key Development Tasks

When implementing features:
1. Blender add-ons must be compatible with Blender's Python API and addon requirements
2. The remote control package should provide a clean Python API for external use
3. MCP server integration should handle communication reliably
4. CLI tools should follow standard command-line conventions

## Important Notes

- This is a new project in initial development phase
- The project structure and core modules need to be created
- Development tools (linting, testing, formatting) are configured
- PyPI packaging configuration is set up in pyproject.toml
- Documentation is built with MkDocs Material and deployed to GitHub Pages

## Documentation

- **Documentation Site**: https://igamenovoer.github.io/blender-remote/
- **Local Development**: `pixi run docs-serve` - Serve docs locally with live reload
- **Building**: `pixi run docs` - Build static documentation
- **Deployment**: Automatic via GitHub Actions on main branch updates

## Development Conventions

- `tmp` dir is for everything not intended to be uploaded to git

## Reusable Project Guides

This repository contains two guides that are not directly related to the blender-remote project but are kept for reuse in similar projects:

- **context-dir-guide.md**: Specification for standardized AI-assisted development context directory structure
- **project-init-guide.md**: Guide for creating professional Python library projects with modern development practices

These guides should be updated when improved patterns or practices are discovered, making them available for future projects.