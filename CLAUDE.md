# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Platform Support

**This project supports Windows, Linux, and macOS platforms.** All components are designed to work seamlessly across all operating systems:
- **Windows**: Full support with Windows-specific paths and configurations
- **Linux**: Full support with Unix-style paths and configurations
- **macOS**: Full support with Unix-style paths and configurations (same as Linux)
- Cross-platform compatibility is maintained throughout the codebase

[... existing content remains unchanged ...]

## Project Memories

### Component Architecture and Naming Conventions

**Drop-in replacements** for existing Blender MCP solutions (see `context/summaries/general-rule.md` for complete details):

#### Component Relationships  
- `blender-mcp` / `BlenderAutoMCP` (3rd party) → **`BLD_Remote_MCP`** (our addon replacement)
- `uvx blender-mcp` (3rd party MCP server) → **`uvx blender-remote`** (our MCP server replacement)

#### Our Project Components
- **`BLD_Remote_MCP`** (`src/blender_remote/addon/bld_remote_mcp/`) - Blender addon with background mode support
- **`BlenderRemoteMCPServer`** (`src/blender_remote/mcp_server.py`) - MCP server implementation  
- **`BlenderClientAPI`** (`src/blender_remote/client.py`, `scene_manager.py`) - Direct Python API (bypasses MCP server)
- **`blender-remote-cli`** (`src/blender_remote/cli.py`) - CLI for process management and configuration

#### Key Architecture
```
LLM IDE ←→ uvx blender-remote ←→ BLD_Remote_MCP ←→ Blender
                    ↑                      ↑
              MCP Protocol           TCP (port 6688)
                                         ↑
BlenderClientAPI (Python API) ────────┘
```

### Reference Code Locations
- Blender Python API reference: `context/refcode/blender_python_reference_4_4` (`BlenderPythonDoc`)
- Reference implementations: `context/refcode/blender-mcp`, `context/refcode/blender_auto_mcp` (stable)
- Debugging: Use `BlenderAutoMCP` + `uvx blender-mcp` as stable fallback for testing

### Blender Process Management

**Critical for Development**: You will frequently need to start/stop Blender processes during testing and development.

#### Preferred Method  
- **Use `pixi run python src/blender_remote/cli.py start`** - Creates startup scripts, handles addon installation
- **Blender Path**: 
  - Linux: `/apps/blender-4.4.3-linux-x64/blender`
  - macOS: Default installation location (auto-detected via `blender-remote-cli init`)
  - Windows: Default installation location (auto-detected via `blender-remote-cli init`)
- **CRITICAL: Always use `&`** for background execution - **Blender will quit when Bash command times out without `&`**
- **Environment Variables**: Set `BLD_REMOTE_MCP_START_NOW=true` and `BLD_REMOTE_MCP_PORT=6688` for auto-start
- **Timeout**: Use **10-second timeout** in Bash (NOT 2-minute default) with `&` background execution
- **Kill processes**: `pkill -f blender` (Linux/macOS) or `taskkill /F /IM blender.exe` (Windows)

#### Fallback Testing
```bash
# BlenderAutoMCP fallback
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1
```

## Development Environment

### Package Management
- **Use `pixi` for all Python operations** - DO NOT run Python scripts directly
- **Command pattern**: `pixi run <command>` instead of direct execution
- This ensures consistent dependency management and environment isolation

### Documentation Tools
- **Diagrams**: Use `graphviz` with `dot` command to generate `.svg` files
- **Documentation**: Built with `mkdocs-material` framework
- **JSON Processing**: `jq` command-line tool available for JSON manipulation

### Development Workflow
```bash
# Correct way to run Python scripts
pixi run python script.py

# Generate documentation diagrams  
dot -Tsvg diagram.dot -o diagram.svg

# Process JSON data
jq '.key' data.json
```

### Temporary File Management
- **Temporary Directory**: `<workspace>/tmp` for storing temporary files
- **File Lifecycle**: Directory is deleted frequently - do not store permanent data
- **Organization**: Create subdirectories for different purposes to improve management
- **Usage Pattern**: Ideal for test artifacts, intermediate processing files, debug outputs

```bash
# Example temporary file usage
mkdir -p tmp/test-results
mkdir -p tmp/debug-logs
mkdir -p tmp/export-data
```

### Cross-Platform Considerations
- Do not use unicode emoji in console output, for better cross platform support

[... rest of the existing content remains unchanged ...]