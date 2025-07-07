# Project Memory

## Current Status
blender-remote is in initial development phase with basic project structure set up but core functionality pending implementation.

## Reference Materials Added

### blender-mcp Implementation
**blender-mcp** has been added to `context/refcode/blender-mcp/` as reference code:

### MCP Protocol Specification
**Model Context Protocol specification** has been added to `context/refcode/modelcontextprotocol/` with complete documentation:
- **Latest Spec**: 2025-06-18 version with security best practices
- **Schema Files**: JSON schemas for all protocol versions
- **Documentation**: Complete API reference, architecture guides, tutorials
- **Client/Server Implementation**: Detailed specs for both sides
- **Transport Layer**: Various transport mechanisms (stdio, SSE, WebSocket)
- **Core Concepts**: Tools, resources, prompts, sampling, roots

### Key Components
- **Blender Addon** (`addon.py`): Creates socket server inside Blender (port 12345) to receive and execute commands
- **MCP Server** (`src/blender_mcp/server.py`): Implements Model Context Protocol for AI assistant integration
- **Communication**: JSON-based protocol over TCP sockets
- **Features**: Object manipulation, material control, scene inspection, arbitrary Python code execution

### Architecture Insights
- Socket-based client-server architecture with Blender as server
- MCP protocol wrapper for AI assistant communication
- Supports external integrations (Poly Haven assets, Hyper3D models, Sketchfab)
- Real-time bidirectional communication

### Implementation Patterns
- Blender addon uses `bpy` API extensively for scene manipulation
- Error handling with JSON response format
- Asynchronous operation support
- Plugin architecture for extensibility

## Development Priorities
1. Study blender-mcp implementation patterns
2. Implement core blender_remote library based on reference architecture
3. Create Blender addon following similar socket server pattern
4. Develop MCP server integration
5. Build CLI tools wrapper
6. Add comprehensive testing

## Technical Stack
- Python 3.10+ with pixi environment management
- Blender Python API (bpy)
- Socket-based networking
- MCP (Model Context Protocol)
- PyPI packaging configuration ready

## Next Steps
Use blender-mcp as architectural reference and MCP specification for implementing blender-remote's core functionality while maintaining the planned API design from README.md. The full MCP spec provides authoritative guidance for protocol implementation.