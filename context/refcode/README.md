# Reference Code

This directory contains external, third-party code repositories that are fetched or cloned on demand.

## Purpose

- Provide AI assistants with implementation examples
- Include source code of relevant libraries for deep understanding
- Maintain local copies of important dependencies
- Enable offline code analysis and learning

## Managed Entries

### blender-mcp/
Complete implementation of Blender MCP server with socket-based communication:
- **Upstream**: https://github.com/ahujasid/blender-mcp.git
- **Local path**: `context/refcode/blender-mcp/`
- **Blender Addon** (`addon.py`): Socket server running inside Blender to receive commands
- **MCP Server** (`src/blender_mcp/server.py`): Model Context Protocol implementation
- **Features**: Object manipulation, material control, scene inspection, code execution
- **Integration**: Works with Claude Desktop and Cursor
- **Assets**: Poly Haven integration, Hyper3D model generation, Sketchfab downloads

This serves as the primary reference for implementing blender-remote's MCP integration and Blender addon architecture.

### modelcontextprotocol/
Official Model Context Protocol documentation and specifications:
- **Upstream**: https://github.com/modelcontextprotocol/modelcontextprotocol.git
- **Local path**: `context/refcode/modelcontextprotocol/`
- **Usage**: Protocol specifications, reference documentation

### mcp-sdk/
Official Python SDK for Model Context Protocol:
- **Upstream**: https://github.com/modelcontextprotocol/python-sdk.git
- **Local path**: `context/refcode/mcp-sdk/`
- **Usage**: Python SDK implementation reference

## Bootstrap

To populate this directory with all external references, run:

```bash
bash context/refcode/bootstrap.sh
```

Or on Windows with Git Bash:

```bash
bash context/refcode/bootstrap.sh
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