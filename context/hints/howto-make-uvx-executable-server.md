# How to Make Your Python Package Executable with `uvx`

## Overview

`uvx` is a command provided by the `uv` package manager that allows users to run Python applications directly from PyPI without installing them permanently. When you run `uvx blender-mcp`, it:

1. **Downloads** the package from PyPI (if not cached)
2. **Creates** a temporary isolated environment
3. **Installs** the package and its dependencies
4. **Executes** the package's entry point script
5. **Cleans up** when done

## How `blender-mcp` Works with `uvx`

Let's examine the `blender-mcp` project structure:

### Key Configuration in `pyproject.toml`

```toml
[project]
name = "blender-mcp"
version = "1.2"
# ... other metadata ...

[project.scripts]
blender-mcp = "blender_mcp.server:main"
```

**The magic happens in `[project.scripts]`:**
- **Key** (`blender-mcp`): The command name users will type
- **Value** (`blender_mcp.server:main`): Points to `main()` function in `blender_mcp/server.py`

### Directory Structure

```
blender-mcp/
├── pyproject.toml              # Package configuration
├── main.py                     # Optional top-level entry point
└── src/
    └── blender_mcp/
        ├── __init__.py
        └── server.py           # Contains main() function
```

### Entry Point Function

In `src/blender_mcp/server.py`:

```python
def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
```

## What Happens When You Run `uvx blender-mcp`

1. **Package Resolution**: `uv` looks up `blender-mcp` on PyPI
2. **Environment Creation**: Creates isolated virtual environment
3. **Installation**: Installs `blender-mcp` and dependencies
4. **Script Generation**: Creates executable script that calls `blender_mcp.server:main`
5. **Execution**: Runs the generated script
6. **Cleanup**: Environment persists in cache for future runs

## Making `blender-remote` Work with `uvx`

### Step 1: Update `pyproject.toml`

Add the console script entry point to your `pyproject.toml`:

```toml
[project]
name = "blender-remote"
version = "0.1.0"
# ... existing configuration ...

# Add this section:
[project.scripts]
blender-remote = "blender_remote.cli:main"
```

### Step 2: Create Main CLI Module

Create `src/blender_remote/cli.py`:

```python
"""
Main entry point for blender-remote CLI.
"""

import sys
import argparse
from typing import Optional

def main():
    """Main entry point for the blender-remote CLI."""
    parser = argparse.ArgumentParser(
        description="Remote control Blender from the command line",
        prog="blender-remote"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # Start MCP server command
    server_parser = subparsers.add_parser(
        "server",
        help="Start the MCP server"
    )
    server_parser.add_argument(
        "--port", 
        type=int, 
        default=9876,
        help="Port to listen on (default: 9876)"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check connection status to Blender"
    )
    
    # Execute command
    exec_parser = subparsers.add_parser(
        "exec",
        help="Execute Python code in Blender"
    )
    exec_parser.add_argument(
        "code",
        help="Python code to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "server":
        from blender_remote.server import start_mcp_server
        start_mcp_server(port=args.port)
    elif args.command == "status":
        from blender_remote.client import check_status
        check_status()
    elif args.command == "exec":
        from blender_remote.client import execute_code
        execute_code(args.code)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Step 3: Create Server Module

Create `src/blender_remote/server.py`:

```python
"""
Blender Remote MCP Server implementation.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def start_mcp_server(port: int = 9876):
    """Start the Blender Remote MCP server."""
    print(f"🚀 Starting Blender Remote MCP server on port {port}...")
    
    # Import your existing server implementation
    # For now, this is a placeholder
    try:
        # This would be your actual server implementation
        # Similar to what's in your blender_addon/bld_remote_mcp/__init__.py
        from blender_remote.mcp_service import MCPService
        service = MCPService(port=port)
        service.run()
    except ImportError:
        print("❌ MCP service implementation not found")
        print("Please implement blender_remote.mcp_service module")
        return 1
    
    return 0

if __name__ == "__main__":
    start_mcp_server()
```

### Step 4: Update Package Structure

Move your existing CLI code to the proper location:

```bash
# Move your existing CLI code
mv scripts/cli.py src/blender_remote/cli.py

# Create server module if it doesn't exist
# (incorporate your existing MCP server code)
```

### Step 5: Add Dependencies

Update your `pyproject.toml` dependencies:

```toml
dependencies = [
    "click>=8.0.0",  # For advanced CLI features (optional)
    # Add your MCP server dependencies
    "mcp[cli]>=1.3.0",  # If using MCP framework
    # Other dependencies...
]
```

### Step 6: Test Locally

Before publishing, test locally:

```bash
# Install in development mode
uv pip install -e .

# Test the command
blender-remote --help
blender-remote server --port 9876
```

### Step 7: Publish to PyPI

```bash
# Build the package
uv build

# Publish to PyPI (you'll need PyPI credentials)
uv publish
```

## Advanced Features

### Multiple Entry Points

You can define multiple executable commands:

```toml
[project.scripts]
blender-remote = "blender_remote.cli:main"
blender-remote-server = "blender_remote.server:start_mcp_server"
blender-remote-client = "blender_remote.client:main"
```

### GUI Entry Points

For GUI applications:

```toml
[project.gui-scripts]
blender-remote-gui = "blender_remote.gui:main"
```

### Custom Entry Points

For plugins and extensions:

```toml
[project.entry-points."blender_remote.plugins"]
example_plugin = "blender_remote_plugins.example:ExamplePlugin"
```

## Testing Your `uvx` Command

Once published to PyPI, users can run:

```bash
# Run directly without installation
uvx blender-remote server --port 9876

# Run with specific version
uvx blender-remote@0.1.0 server

# Run from Git (during development)
uvx --from git+https://github.com/yourusername/blender-remote blender-remote server
```

## Comparison with Other Tools

| Tool | Purpose | Command Example |
|------|---------|-----------------|
| `uvx` | Run tools without installing | `uvx blender-remote server` |
| `pipx` | Install tools in isolated environments | `pipx install blender-remote` |
| `uv tool install` | Install tools with uv | `uv tool install blender-remote` |
| `pip install` | Install in current environment | `pip install blender-remote` |

## Benefits of `uvx` Support

1. **Zero Installation Friction**: Users can try your tool instantly
2. **Isolation**: No dependency conflicts with user's environment
3. **Version Flexibility**: Easy to test different versions
4. **CI/CD Friendly**: Great for automated workflows
5. **Cross-Platform**: Works consistently across operating systems

## Implementation with FastMCP

### What is FastMCP?

[FastMCP](https://github.com/jlowin/fastmcp) is a high-level Python framework that makes building MCP (Model Context Protocol) servers simple and intuitive. It's designed to eliminate the boilerplate required for implementing the MCP protocol directly.

### Why Use FastMCP for Blender Remote?

FastMCP provides several advantages for implementing your MCP server:

1. **Pythonic Interface**: Write tools using simple decorators (`@mcp.tool()`, `@mcp.resource()`)
2. **Protocol Handling**: Automatically handles JSON-RPC, session state, and MCP formatting
3. **Built-in Transport Support**: Supports STDIO (for Claude Desktop), SSE, WebSockets
4. **Type Safety**: Automatically generates schemas from Python type hints
5. **uvx Ready**: Can be packaged and executed with `uvx` out of the box

### FastMCP Implementation for Blender Remote

#### Step 1: Add FastMCP Dependencies

Update your `pyproject.toml`:

```toml
[project]
name = "blender-remote"
version = "0.1.0"
# ... existing configuration ...

dependencies = [
    "fastmcp>=2.0.0",  # Core FastMCP framework
    # Add your existing dependencies
]

# Add the console script entry point:
[project.scripts]
blender-remote = "blender_remote.server:main"
```

#### Step 2: Create FastMCP Server Module

Create `src/blender_remote/server.py`:

```python
"""
FastMCP server implementation for Blender Remote.
"""

import asyncio
import socket
import json
import logging
from typing import Optional, Dict, Any

from fastmcp import FastMCP, Context, Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP("Blender Remote MCP")

class BlenderConnection:
    """Handle connection to Blender TCP server."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        self.host = host
        self.port = port
        self.sock = None
    
    async def connect(self) -> bool:
        """Connect to Blender addon."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {e}")
            self.sock = None
            return False
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to Blender and get response."""
        if not self.sock:
            if not await self.connect():
                raise ConnectionError("Cannot connect to Blender")
        
        try:
            # Send command
            message = json.dumps(command)
            self.sock.send(message.encode() + b'\n')
            
            # Receive response
            response = b""
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                try:
                    data = json.loads(response.decode())
                    return data
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error communicating with Blender: {e}")
            self.sock = None
            raise

# Global connection instance
blender_conn = BlenderConnection()

@mcp.tool()
async def get_scene_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the current Blender scene."""
    await ctx.info("Getting scene information from Blender...")
    
    try:
        response = await blender_conn.send_command({
            "type": "get_scene_info",
            "params": {}
        })
        return response
    except Exception as e:
        await ctx.error(f"Failed to get scene info: {e}")
        raise

@mcp.tool()
async def execute_blender_code(code: str, ctx: Context) -> Dict[str, Any]:
    """Execute Python code in Blender."""
    await ctx.info(f"Executing code in Blender...")
    
    try:
        response = await blender_conn.send_command({
            "type": "execute_code",
            "params": {"code": code}
        })
        return response
    except Exception as e:
        await ctx.error(f"Failed to execute code: {e}")
        raise

@mcp.tool()
async def get_object_info(object_name: str, ctx: Context) -> Dict[str, Any]:
    """Get detailed information about a specific object in Blender."""
    await ctx.info(f"Getting info for object: {object_name}")
    
    try:
        response = await blender_conn.send_command({
            "type": "get_object_info",
            "params": {"object_name": object_name}
        })
        return response
    except Exception as e:
        await ctx.error(f"Failed to get object info: {e}")
        raise

@mcp.tool()
async def get_viewport_screenshot(ctx: Context) -> Image:
    """Capture a screenshot of the Blender viewport."""
    await ctx.info("Capturing viewport screenshot...")
    
    try:
        response = await blender_conn.send_command({
            "type": "get_viewport_screenshot",
            "params": {}
        })
        
        if response.get("status") == "success":
            # Assuming response contains base64 image data
            import base64
            image_data = base64.b64decode(response["image_data"])
            return Image(data=image_data, format="png")
        else:
            raise ValueError(response.get("message", "Screenshot failed"))
            
    except Exception as e:
        await ctx.error(f"Failed to capture screenshot: {e}")
        raise

@mcp.resource("blender://status")
async def blender_status() -> Dict[str, Any]:
    """Get the current status of the Blender connection."""
    try:
        if blender_conn.sock:
            return {"status": "connected", "host": blender_conn.host, "port": blender_conn.port}
        else:
            return {"status": "disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.prompt()
def blender_workflow_start() -> str:
    """Initialize a Blender workflow session."""
    return """I'm ready to help you work with Blender! I can:

1. **Get Scene Info**: View current scene objects and properties
2. **Execute Code**: Run Python scripts in Blender  
3. **Get Object Info**: Inspect specific objects in detail
4. **Take Screenshots**: Capture viewport images
5. **Check Status**: Monitor connection to Blender

What would you like to do with your Blender scene?"""

def main():
    """Main entry point for uvx execution."""
    # This is the function called when running `uvx blender-remote`
    mcp.run()

if __name__ == "__main__":
    main()
```

#### Step 3: Create CLI Module (Optional)

For compatibility with the existing guide, create `src/blender_remote/cli.py`:

```python
"""
CLI interface - delegates to FastMCP server.
"""

from .server import main

# For backward compatibility with the original guide
if __name__ == "__main__":
    main()
```

#### Step 4: Update Package Structure

Ensure your `src/blender_remote/__init__.py` exports the main function:

```python
"""Blender Remote Control Package."""

__version__ = "0.1.0"

# Import main components for easy access
from .server import main

__all__ = ["main"]
```

### Usage with LLM-Assisted IDEs

After publishing to PyPI, users can add your server to their LLM IDE configuration:

#### VS Code (with Cline/Claude Dev):

```json
{
  "mcp": {
    "blender-remote": {
      "type": "stdio",
      "command": "uvx",
      "args": ["blender-remote"]
    }
  }
}
```

#### Claude Desktop:

```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx",
      "args": ["blender-remote"]
    }
  }
}
```

### FastMCP Benefits for Your Use Case

1. **Protocol Compatibility**: FastMCP ensures your server is fully compatible with the MCP specification
2. **Context Support**: Built-in logging, progress reporting, and error handling via `Context`
3. **Type Safety**: Automatic schema generation from type hints
4. **Image Handling**: Built-in support for returning images (screenshots)
5. **Resource Templates**: Dynamic resources for object-specific data
6. **Prompt Templates**: Guide users on how to use your tools effectively

### Testing Your FastMCP Server

FastMCP provides excellent development tools:

```bash
# Development mode with MCP Inspector
fastmcp dev src/blender_remote/server.py

# Install for Claude Desktop
fastmcp install src/blender_remote/server.py --name "Blender Remote"

# Test locally
python -m blender_remote.server
```

## Complete Example Integration

For your `blender-remote` project, the minimal changes needed:

1. **Add to `pyproject.toml`**:
```toml
[project.scripts]
blender-remote = "blender_remote.server:main"

dependencies = [
    "fastmcp>=2.0.0",
]
```

2. **Create `src/blender_remote/server.py`** with FastMCP implementation (see above)

3. **Update `src/blender_remote/__init__.py`**:
```python
"""Blender Remote Control Package."""

__version__ = "0.1.0"

from .server import main

__all__ = ["main"]
```

After these changes and publishing to PyPI, users can run:

```bash
uvx blender-remote
```

This will start your Blender Remote MCP server and make it available to any MCP-compatible LLM client!
