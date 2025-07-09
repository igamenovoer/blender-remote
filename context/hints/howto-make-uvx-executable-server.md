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

## Complete Example Integration

For your `blender-remote` project, the minimal changes needed:

1. **Add to `pyproject.toml`**:
```toml
[project.scripts]
blender-remote = "blender_remote.cli:main"
```

2. **Create `src/blender_remote/cli.py`** with the main function

3. **Ensure proper imports** in `src/blender_remote/__init__.py`:
```python
"""Blender Remote Control Package."""

__version__ = "0.1.0"

# Import main components for easy access
from .cli import main

__all__ = ["main"]
```

After these changes and publishing to PyPI, users can run:

```bash
uvx blender-remote server --port 9876
```

This will start your Blender Remote MCP server without any installation required!
