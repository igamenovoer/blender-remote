# Blender Add-ons

This directory contains Blender add-ons (plugins) that are installed directly into Blender.

## Purpose

These add-ons create non-stop services inside Blender that:
- Listen for incoming commands from the remote control library
- Execute commands using Blender's Python API
- Send responses back to the remote controller
- Maintain persistent connections for real-time control

## Structure

Each add-on should be in its own subdirectory with:
- `__init__.py` - Add-on metadata and registration
- Service implementation for receiving and executing commands
- Blender operator definitions for various operations

## Installation

These add-ons are installed through Blender's preferences:
1. Open Blender
2. Go to Edit > Preferences > Add-ons
3. Click "Install" and select the add-on .zip file
4. Enable the add-on by checking its checkbox

## Development

When developing add-ons:
- Follow Blender's add-on conventions and best practices
- Ensure compatibility with Blender's Python API version
- Test thoroughly within Blender's environment
- Handle errors gracefully to avoid crashing Blender