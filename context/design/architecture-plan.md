# HEADER
- **Created**: 2025-07-07 19:18:00
- **Modified**: 2025-07-08 16:20:00
- **Summary**: Architecture plan for blender-remote project combining reference implementation best practices for comprehensive remote Blender control.

# Blender Remote Architecture Plan

## Overview

The blender-remote project implements a comprehensive system for remote Blender control combining the best practices from both reference implementations:
- Background-safe service patterns from blender-echo-plugin
- MCP protocol integration from blender-mcp
- Clean API design for PyPI distribution

## Core Architecture

### 1. Blender Addon (`blender_addon/`)

**Background-Safe MCP Server Addon**
```
blender_addon/
├── __init__.py                 # Main addon registration
├── blender_remote_server/
│   ├── __init__.py            # Addon implementation
│   ├── async_loop.py          # Asyncio integration (from echo-plugin)
│   ├── mcp_server.py          # MCP server implementation 
│   ├── command_handlers.py    # Blender command execution
│   └── launcher.py            # External script support
```

**Key Features:**
- Uses asyncio event loop integration from blender-echo-plugin for background safety
- Implements MCP protocol using FastMCP framework
- Supports both GUI and `blender --background` modes
- Executes commands safely via `bpy.app.timers.register()`
- Handles graceful shutdown and cleanup

**MCP Tools to Implement:**
- `execute_python_code` - Execute arbitrary Python code in Blender
- `get_scene_info` - Get current scene state and object list
- `get_object_info` - Get detailed object information
- `create_primitive` - Create basic meshes (cube, sphere, etc.)
- `modify_object` - Transform, scale, rotate objects
- `render_scene` - Trigger rendering operations
- `export_scene` - Export to various formats
- `import_asset` - Import external assets

### 2. Remote Control Library (`src/blender_remote/`)

**Python Package for External Control**
```
src/blender_remote/
├── __init__.py               # Main API exports
├── client.py                 # MCP client connection
├── commands/
│   ├── __init__.py
│   ├── scene.py             # Scene manipulation commands
│   ├── objects.py           # Object manipulation commands
│   ├── rendering.py         # Rendering commands
│   └── io.py                # Import/export commands
├── connection.py            # Connection management
└── exceptions.py            # Custom exceptions
```

**API Design:**
```python
import blender_remote

# Connect to running Blender instance
client = blender_remote.connect(port=8080)

# High-level operations
scene = client.scene.get_info()
cube = client.objects.create_cube(location=(0, 0, 0))
client.rendering.render_frame()

# Low-level code execution
client.execute("bpy.ops.mesh.primitive_cube_add()")
```

### 3. CLI Tools (`scripts/`)

**Command-Line Interface**
```
scripts/
├── blender-remote              # Main CLI entry point
├── start-blender-server        # Start Blender with addon
├── render-remote               # Remote rendering utility
└── scene-export               # Scene export utility
```

**CLI Usage:**
```bash
# Start Blender server
blender-remote start --port 8080 --background

# Execute commands
blender-remote exec "bpy.ops.mesh.primitive_cube_add()"

# Render remotely  
blender-remote render --output /path/to/output.png

# Scene operations
blender-remote scene list-objects
blender-remote object create cube --location 0,0,0
```

## Technical Implementation Details

### Connection Architecture

**Process Communication:**
```
┌─────────────────┐    MCP/JSON-RPC    ┌──────────────────┐
│  External       │ ◄───────────────── │  Blender Process │
│  Python Client  │                    │  + MCP Server    │
│  (blender_remote)│ ──────────────────► │  + Addon         │
└─────────────────┘                    └──────────────────┘
```

**Connection Methods:**
1. **TCP Socket** (primary) - Direct TCP connection for local/remote use
2. **Named Pipes** (future) - OS-specific IPC for local communication
3. **WebSocket** (future) - Browser-based control interfaces

### Background Safety Patterns

**Event Loop Integration:**
- Use `kick_async_loop()` pattern from blender-echo-plugin
- Modal operator for event loop management in GUI mode
- External launcher script for background mode

**Thread-Safe Execution:**
- All `bpy.*` operations via `bpy.app.timers.register()`
- Async command queuing with proper response handling
- Exception isolation and error reporting

**Resource Access:**
- Avoid `bpy.context` in background mode
- Use `bpy.data.*` for direct data access
- Handle missing GUI elements gracefully

### MCP Protocol Integration

**Server Implementation:**
- FastMCP framework for protocol handling
- Tool-based command structure
- Proper error handling and response formatting
- Connection lifecycle management

**Message Flow:**
```
Client Request → MCP Tool → Background Thread → Main Thread Timer → Blender API → Response
```

### Addon Installation & Management

**Installation Methods:**
1. **Programmatic** - Via blender_remote package
2. **Manual** - Traditional Blender addon installation
3. **CLI** - Via blender-remote command-line tool

**Auto-Discovery:**
- Environment variable configuration
- Default port conventions
- Service registration patterns

## Development Phases

### Phase 1: Core Infrastructure
1. Blender addon with background-safe MCP server
2. Basic remote client library
3. Simple CLI tool for testing

### Phase 2: Command Library
1. Scene manipulation commands
2. Object creation and modification
3. Rendering operations

### Phase 3: Advanced Features
1. Asset import/export
2. Advanced rendering controls
3. Plugin system for custom commands

### Phase 4: Production Features
1. Connection pooling
2. Authentication/security
3. Performance optimization
4. Documentation and examples

## Security Considerations

**Code Execution Safety:**
- Sandbox option for restricted environments
- Command validation and filtering
- User permission controls

**Network Security:**
- Local-only binding by default
- Optional authentication mechanisms
- Encrypted connections for remote access

## Testing Strategy

**Test Structure:**
```
tests/
├── unit/
│   ├── test_client.py
│   ├── test_commands.py
│   └── test_connection.py
├── integration/
│   ├── test_addon_integration.py
│   └── test_full_workflow.py
└── fixtures/
    ├── test_scenes/
    └── reference_outputs/
```

**Testing Approach:**
- Unit tests for client library
- Integration tests with actual Blender instances
- Automated CI with headless Blender
- Performance benchmarks

This architecture leverages the proven patterns from both reference implementations while providing a clean, production-ready API for remote Blender control.