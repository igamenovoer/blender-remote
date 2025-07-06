# CLI Scripts

This directory contains command-line interface tools for controlling Blender remotely.

## Purpose

These scripts provide:
- Command-line access to Blender remote control functionality
- Batch processing capabilities
- Integration with shell scripts and automation workflows
- Quick access to common Blender operations

## Usage Examples

```bash
# Connect to Blender and execute a command
blender-remote execute "bpy.ops.mesh.primitive_cube_add()"

# Render a specific frame
blender-remote render --frame 1 --output render.png

# Run a Python script in Blender
blender-remote run-script my_script.py

# Check connection status
blender-remote status
```

## Structure

Each script should:
- Use argparse for command-line argument parsing
- Import and use the blender_remote package
- Provide clear help messages and documentation
- Handle errors gracefully with informative messages

## Installation

These scripts will be registered as console entry points in pyproject.toml, making them available system-wide after package installation:

```bash
pip install blender-remote
# Now 'blender-remote' command is available globally
```