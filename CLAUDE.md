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

## Available MCP Servers

- **tavily**: `bunx -y tavily-mcp@latest` - Web search and content extraction
- **fetch**: `uvx mcp-server-fetch` - URL fetching capabilities
- **blender-mcp**: `uvx blender-mcp` - Blender integration tools
- **context7**: `bunx -y @upstash/context7-mcp` - Context and documentation management

## MCP Protocol Reference

For MCP protocol details and implementation guidance:
1. **First check**: `context/summaries/mcp-implementation-guide.md` for essential implementation details
2. **Query context7**: Use `mcp__context7__resolve-library-id` + `mcp__context7__get-library-docs` for latest protocol specs
3. **Reference code**: Check `context/refcode/modelcontextprotocol/` for complete protocol documentation

## Blender MCP Reference Implementations

For Blender addon patterns and MCP integration examples:

### Primary Reference: blender_auto_mcp
- **Location**: `context/refcode/blender_auto_mcp/`
- **Description**: Production-ready 3rd party Blender MCP addon (GUI mode only)
- **Operational Status**: 
  - ✅ Installed and running on port 9876
  - ⚠️ **Limitation**: Only works in GUI mode, not in `blender --background`
- **Key Components**:
  - `server.py`: Core MCP server implementation (**PRIMARY ARCHITECTURE REFERENCE**)
  - `asset_providers.py`: 3rd party integrations (PolyHaven, Hyper3D, Sketchfab) - **NOT NEEDED**
  - `ui_panel.py`: GUI controls
  - `utils.py`: Helper functions
- **Environment Variables**: 
  - `BLENDER_AUTO_MCP_SERVICE_PORT=9876` (default port)
  - `BLENDER_AUTO_MCP_START_NOW=1` (auto-start)
- **Client Interaction**: Via `context/refcode/auto_mcp_remote/` modules
- **Usage**: For MCP integration via `uvx blender-mcp` (interfaces with this implementation)

### Secondary References
- **blender-echo-plugin**: `context/refcode/blender-echo-plugin/` - Simple TCP server pattern for background services
- **blender-mcp**: `context/refcode/blender-mcp/` - Original monolithic implementation (deprecated in favor of blender_auto_mcp)

## Architecture Overview

1. **Blender Add-ons** (`blender_addon/`): Multiple add-ons that create non-stop services inside Blender. These services listen for commands and execute them using Blender's Python API.

2. **Remote Control Library** (`src/blender_remote/`): Python package used outside of Blender to connect to the add-ons and control Blender. Usage pattern: `import blender_remote.xxxx`

3. **MCP Server Integration**: Provides the communication protocol between the remote control library and Blender add-ons.

4. **CLI Tools** (`scripts/`): Command-line interface tools for remote Blender control operations.

## Current Development Focus: Minimal Background-Compatible MCP Service

### Active Task: `context/tasks/blender-bg-mcp/goal.md`
We are developing a minimal MCP service that:
- **Works like BlenderAutoMCP** but supports both GUI and background modes
- **Essential functions only**: connection management, code execution, scene operations
- **No 3rd party assets**: Excludes PolyHaven, Hyper3D, Sketchfab integrations
- **Same interaction pattern**: Compatible with BlenderAutoMCP client code
- **Background mode support**: Works in `blender --background` via asyncio

### Architecture References
- **Primary**: `context/refcode/blender_auto_mcp/server.py` - BlenderAutoMCPServer class
- **Essential Handlers**: execute_code, get_scene_info, get_object_info, get_viewport_screenshot, server_shutdown
- **Client Pattern**: `context/refcode/auto_mcp_remote/` - How to interact with the service
- **Background Integration**: Needs asyncio event loop for headless operation

## Key Development Tasks

When implementing features:
1. Blender add-ons must be compatible with Blender's Python API and addon requirements
2. The remote control package should provide a clean Python API for external use
3. MCP server integration should handle communication reliably
4. CLI tools should follow standard command-line conventions
5. **NEW**: Background mode compatibility requires asyncio integration patterns

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

## Blender Process Management

**Blender Path**: `/apps/blender-4.4.3-linux-x64/blender`

### Starting Blender with Auto MCP
```bash
# Kill any existing Blender processes
pkill -f blender

# Start with auto-start MCP (GUI mode recommended)
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1
/apps/blender-4.4.3-linux-x64/blender &

# Wait ~10 seconds for startup (not 2 minutes!)
sleep 10
```

### Testing MCP Connection
```python
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 9876))
command = {"type": "get_scene_info", "params": {}}
sock.sendall(json.dumps(command).encode('utf-8'))
response = json.loads(sock.recv(4096).decode('utf-8'))
sock.close()
```

### Process Management
- **GUI Mode**: Blender stays running until killed - use this for testing
- **Background Mode**: Exits immediately without blocking operation (needs asyncio loop)
- **Check Running**: `ps aux | grep blender | grep -v grep`
- **Check Port**: `netstat -tlnp | grep 9876`
- **Kill Process**: `kill <PID>` or `pkill -f blender`

## Reusable Project Guides

This repository contains two guides that are not directly related to the blender-remote project but are kept for reuse in similar projects:

- **context-dir-guide.md**: Specification for standardized AI-assisted development context directory structure
- **project-init-guide.md**: Guide for creating professional Python library projects with modern development practices

These guides should be updated when improved patterns or practices are discovered, making them available for future projects.

## Blender Configuration

- Blender path is `/apps/blender-4.4.3-linux-x64/blender`, you can start it yourself

## Implementation Hints

- blender will not exit in GUI mode unless you kill it, so DO NOT wait for it to finish, just read its console output on-the-fly

## Blender Development Notes

- blender is not very good at cleaning up its internal states, so if anything goes weird, consider restart blender and re-install the plugin under development
- **If blender addon is updated, copy it to the blender plugin dir to make it effective**

## BLD Remote MCP Service Status

**Service Status**: ✅ FULLY OPERATIONAL (as of 2025-07-08)

**Installation**: 
- Plugin permanently installed at `/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/`
- Auto-loads on Blender startup
- Available as `import bld_remote` API

**Key Fix Applied**: 
- Issue: `start_mcp_service()` scheduled asyncio task but modal operator wasn't started
- Solution: Added `async_loop.ensure_async_loop()` call in `start_server_from_script()`
- Result: Service now starts properly and `get_status()` reports running correctly

**Service Configuration**:
- Default port: 6688 (configurable via `BLD_REMOTE_MCP_PORT`)
- Protocol: JSON TCP (`{"message": "...", "code": "..."}`)
- Auto-start: Controlled by `BLD_REMOTE_MCP_START_NOW` environment variable

**Testing Verified**:
- ✅ Basic TCP connection and message processing
- ✅ Python code execution in Blender context
- ✅ Blender API access and scene manipulation
- ✅ Multiple concurrent connections (stress tested)
- ✅ Large code blocks and error handling
- ✅ Service stability under load

**Usage**:
```python
import bld_remote
bld_remote.start_mcp_service()  # Start on port 6688
status = bld_remote.get_status()  # Check if running
```

**Logs**: See `context/logs/2025-07-08_bld-remote-mcp-service-implementation-success.md` for complete implementation details.

## Multiple MCP Services Overview

This project now involves **TWO separate MCP services**:

### 1. BlenderAutoMCP (3rd Party - Reference)
- **Location**: Installed system-wide in Blender
- **Port**: 9876
- **Status**: ✅ Operational, GUI mode only
- **Purpose**: Reference implementation and comparison
- **Limitation**: Cannot run in `blender --background`
- **Features**: Full-featured with 3rd party asset providers

### 2. BLD Remote MCP (Our Implementation) 
- **Location**: `blender_addon/bld_remote_mcp/`
- **Port**: 6688 
- **Status**: ✅ Operational, both GUI and background modes
- **Purpose**: Minimal essential MCP service
- **Goal**: Background mode compatibility for headless applications
- **Features**: Essential handlers only (no 3rd party assets)

### Development Strategy
- **Use BlenderAutoMCP** as architectural reference (`server.py`)
- **Build BLD Remote MCP** with same client interaction patterns
- **Focus on minimal essential functions** for background mode compatibility
- **Test both services** to ensure they don't conflict (different ports)

## Development Guidance

- **DO NOT commit to git unless I told you to**

## Project Memories

- We will refer to our in-development plugin as `BLD_Remote_MCP`
- We will refer to the reference implementation which is also running in blender as `BlenderAutoMCP`

## CRITICAL: Blender Process Management Rules

- **TIMEOUT REQUIREMENT**: When starting Blender with Bash() command, ALWAYS set timeout to 10 seconds maximum
- **NEVER use long timeouts**: NEVER set timeout to 2 minutes (120 seconds) or any long duration
- **Background execution**: Always start Blender in shell background (with `&`)
- **Quick startup verification**: Wait exactly 10 seconds after start, then read console output
- **Both modes**: This applies to GUI mode (`blender`) and background mode (`blender --background`)

### Correct Bash Command Pattern:
```bash
# CORRECT - 10 second timeout
Bash(command="blender &", timeout=10000)  # 10 seconds = 10000ms

# WRONG - Never do this
Bash(command="blender &", timeout=120000)  # 2 minutes = 120000ms
```

**Rationale**: Blender starts quickly (~5-10 seconds) but runs indefinitely. Long timeouts waste time and provide no benefit since Blender doesn't exit on its own in GUI mode.