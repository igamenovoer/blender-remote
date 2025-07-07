# Reference Code

This directory contains reference code repositories included as git submodules.

## Purpose

- Provide AI assistants with implementation examples
- Include source code of relevant libraries for deep understanding
- Maintain local copies of important dependencies
- Enable offline code analysis and learning

## Current References

### blender-mcp/
Complete implementation of Blender MCP server with socket-based communication:
- **Blender Addon** (`addon.py`): Socket server running inside Blender to receive commands
- **MCP Server** (`src/blender_mcp/server.py`): Model Context Protocol implementation
- **Features**: Object manipulation, material control, scene inspection, code execution
- **Integration**: Works with Claude Desktop and Cursor
- **Assets**: Poly Haven integration, Hyper3D model generation, Sketchfab downloads

This serves as the primary reference for implementing blender-remote's MCP integration and Blender addon architecture.

## Submodules

Reference repositories might include:
- Blender Python API examples
- MCP server implementations
- Similar remote control projects
- Python packaging examples

## Adding Submodules

```bash
# Add a new reference repository
git submodule add https://github.com/example/repo.git refcode/repo-name

# Initialize after cloning
git submodule update --init --recursive
```

## Usage Guidelines

1. **Read-Only**: These are reference materials - never modify
2. **Version Pinning**: Keep submodules at stable versions
3. **Documentation**: Note why each reference was included
4. **Licensing**: Ensure compliance with source licenses

## Organization

Group references by purpose:
- `blender/` - Blender-related references
- `mcp/` - MCP protocol implementations
- `python/` - Python best practices examples
- `similar_projects/` - Related remote control projects

## Maintenance

Periodically update submodules to latest stable versions:
```bash
git submodule update --remote
```