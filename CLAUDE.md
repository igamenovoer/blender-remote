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
- Development tools (linting, testing, formatting) need to be configured
- PyPI packaging configuration needs to be set up in pyproject.toml

## Development Conventions

- `tmp` dir is for everything not intended to be uploaded to git