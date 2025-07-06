# Blender Remote Control Library

This directory contains the Python package for remotely controlling Blender from outside the Blender environment.

## Purpose

This package provides a Python API for:
- Connecting to Blender add-ons running inside Blender
- Sending commands to control Blender operations
- Receiving responses and data from Blender
- Managing MCP (Model Context Protocol) server connections

## Usage

```python
import blender_remote
from blender_remote import BlenderConnection

# Connect to a running Blender instance
connection = BlenderConnection(host='localhost', port=5555)

# Send commands to Blender
connection.create_object('Cube', location=(0, 0, 0))
connection.render_frame(output_path='render.png')
```

## Structure

- Core connection and communication modules
- Command builders and parsers
- MCP protocol implementation
- Utility functions for common operations
- Error handling and retry logic

## Installation

This package will be available via pip:
```bash
pip install blender-remote
```

For development:
```bash
pip install -e .
```

## Note on Src Layout

This package uses the "src layout" which is the recommended structure for Python packages in 2024. The src layout:
- Ensures tests run against the installed version of the package
- Provides better isolation of the package code
- Follows modern Python packaging best practices
- Is recommended by the Python Packaging Authority (PyPA)