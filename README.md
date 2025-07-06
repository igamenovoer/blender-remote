# blender-remote

Remote control Blender with Python and MCP server

## Overview

blender-remote enables you to control Blender remotely through a Python API and command-line tools. It consists of:

- **Blender Add-ons**: Install these in Blender to enable remote control capabilities
- **Python Library**: Control Blender from any Python script or application
- **CLI Tools**: Command-line interface for quick Blender operations
- **MCP Server**: Model Context Protocol integration for AI-assisted workflows

## Installation

### From PyPI (Coming Soon)

```bash
pip install blender-remote
```

### From Source

```bash
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote
pip install -e .
```

## Quick Start

### 1. Install Blender Add-on

1. Download the add-on from the `blender_addon/` directory
2. In Blender: Edit → Preferences → Add-ons → Install
3. Select the add-on file and enable it

### 2. Connect from Python

```python
import blender_remote

# Connect to Blender
client = blender_remote.connect("localhost", 5555)

# Create a cube
client.create_primitive("cube", location=(0, 0, 0))

# Render the scene
client.render("output.png")
```

### 3. Use CLI Tools

```bash
# Check connection
blender-remote status

# Execute Blender Python code
blender-remote exec "bpy.ops.mesh.primitive_cube_add()"

# Render current scene
blender-remote render --output render.png
```

## Features

- **Real-time Control**: Send commands and receive responses instantly
- **Python API**: Full-featured Python library for complex automations
- **CLI Tools**: Quick command-line access to common operations
- **MCP Integration**: Compatible with AI coding assistants
- **Extensible**: Easy to add custom commands and operations

## Development

This project uses [pixi](https://pixi.sh) for environment management:

```bash
# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Create development environment
pixi install

# Run tests
pixi run pytest
```

## Project Structure

```
blender-remote/
├── blender_addon/     # Blender add-ons
├── src/               # Source code (src layout)
│   └── blender_remote/    # Python library
├── scripts/          # CLI tools
├── tests/           # Test suite
├── context/         # AI assistant resources
└── docs/            # Documentation
```

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to our repository.

## License

[MIT License](LICENSE)

## Support

- [Documentation](https://igamenovoer.github.io/blender-remote/)
- [Issue Tracker](https://github.com/igamenovoer/blender-remote/issues)
- [Discussions](https://github.com/igamenovoer/blender-remote/discussions)