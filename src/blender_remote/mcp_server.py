"""
FastMCP server implementation for Blender Remote.

This module provides a Model Context Protocol (MCP) server that connects to
the BLD_Remote_MCP service running inside Blender. This allows LLM IDEs to
control Blender through the MCP protocol.

Architecture:
    IDE/Client → MCP Server (this, HTTP/MCP) → BLD_Remote_MCP (TCP) → Blender

Usage:
    uvx blender-remote                                  # Default: MCP server on 8000, connects to Blender TCP on 6688
    uvx blender-remote --blender-port 7777              # Connect to Blender TCP on port 7777
    uvx blender-remote --mcp-port 9000                  # Run MCP server on port 9000
    uvx blender-remote --blender-host 192.168.1.100    # Connect to remote Blender instance

This will start an MCP server (HTTP) that communicates with Blender's BLD_Remote_MCP service (TCP).
"""

import argparse
import asyncio
import json
import logging
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, cast

from fastmcp import FastMCP, Context
from fastmcp.utilities.types import Image

# Import config manager for reading default port
try:
    from .cli import BlenderRemoteConfig
except ImportError:
    # Handle case where we're running standalone
    from blender_remote.cli import BlenderRemoteConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_default_blender_port() -> int:
    """Get default Blender TCP port from config file, fallback to 6688."""
    try:
        config = BlenderRemoteConfig()
        port = config.get("mcp_service.default_port")
        if port and isinstance(port, int):
            return port
    except Exception as e:
        logger.debug(f"Could not read config file: {e}")
    
    # Fallback to default
    return 6688


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for MCP server and Blender connection."""
    parser = argparse.ArgumentParser(
        description="Blender Remote MCP Server - Connect LLM IDEs to Blender"
    )
    
    # MCP Server configuration (where this FastMCP server runs)
    parser.add_argument(
        "--mcp-host",
        default="127.0.0.1",
        help="Host address for the MCP server to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=8000,
        help="Port for the MCP server to bind to (default: 8000)"
    )
    
    # Blender connection configuration (where BLD_Remote_MCP TCP server runs)
    parser.add_argument(
        "--blender-host",
        default="127.0.0.1",
        help="Host address to connect to Blender BLD_Remote_MCP TCP service (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--blender-port",
        type=int,
        default=None,
        help="Port to connect to Blender BLD_Remote_MCP TCP service (default: from config or 6688)"
    )
    
    # Legacy arguments for backward compatibility
    parser.add_argument(
        "--host",
        default=None,
        help="Legacy: same as --blender-host"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Legacy: same as --blender-port"
    )
    
    return parser.parse_args()


# Create the FastMCP server instance
mcp: FastMCP = FastMCP("Blender Remote MCP")


class BlenderConnection:
    """Handle connection to Blender BLD_Remote_MCP TCP server."""

    def __init__(self, blender_host: str = "127.0.0.1", blender_port: int = 6688):
        self.blender_host = blender_host
        self.blender_port = blender_port
        self.sock: Optional[socket.socket] = None

    async def connect(self) -> bool:
        """Connect to Blender BLD_Remote_MCP TCP server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.blender_host, self.blender_port))
            logger.info(
                f"Connected to Blender BLD_Remote_MCP TCP server at {self.blender_host}:{self.blender_port}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender BLD_Remote_MCP TCP server: {e}")
            self.sock = None
            return False

    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to Blender and get response."""
        if not self.sock:
            if not await self.connect():
                raise ConnectionError(
                    "Cannot connect to Blender BLD_Remote_MCP TCP service"
                )

        # At this point, self.sock should not be None
        assert self.sock is not None

        try:
            # Send command
            message = json.dumps(command)
            self.sock.sendall(message.encode("utf-8"))

            # Receive response
            response_data = self.sock.recv(8192)
            if not response_data:
                raise ConnectionError("Connection closed by Blender")

            response = json.loads(response_data.decode("utf-8"))
            return cast(Dict[str, Any], response)

        except Exception as e:
            logger.error(f"Error communicating with Blender: {e}")
            # Close and reset connection on error
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
            raise


# Global connection instance (will be initialized in main())
blender_conn: Optional[BlenderConnection] = None


@mcp.tool()
async def get_scene_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the current Blender scene."""
    await ctx.info("Getting scene information from Blender...")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "get_scene_info", "params": {}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Blender error: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        return cast(Dict[str, Any], response.get("result", {}))
    except Exception as e:
        await ctx.error(f"Failed to get scene info: {e}")
        return {"error": str(e)}


@mcp.tool()
async def execute_blender_code(code: str, ctx: Context) -> Dict[str, Any]:
    """Execute Python code in Blender."""
    await ctx.info(f"Executing code in Blender...")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "execute_code", "params": {"code": code}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Code execution failed: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        return cast(
            Dict[str, Any],
            response.get("result", {"message": "Code executed successfully"}),
        )
    except Exception as e:
        await ctx.error(f"Failed to execute code: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_object_info(object_name: str, ctx: Context) -> Dict[str, Any]:
    """Get detailed information about a specific object in Blender."""
    await ctx.info(f"Getting info for object: {object_name}")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "get_object_info", "params": {"object_name": object_name}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Failed to get object info: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        return cast(Dict[str, Any], response.get("result", {}))
    except Exception as e:
        await ctx.error(f"Failed to get object info: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_viewport_screenshot(
    ctx: Context,
    max_size: int = 800,
    filepath: Optional[str] = None,
    format: str = "png",
) -> Dict[str, Any]:
    """Capture a screenshot of the Blender viewport and return as base64 encoded data. Note: Only works in GUI mode."""
    await ctx.info("Capturing viewport screenshot...")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {
                "type": "get_viewport_screenshot",
                "params": {
                    "max_size": max_size,
                    "format": format,
                    # Don't provide filepath - let Blender generate unique UUID filename
                },
            }
        )

        if response.get("status") == "error":
            error_msg = response.get("message", "Unknown error")
            await ctx.error(f"Screenshot failed: {error_msg}")
            return {"error": error_msg}

        result = response.get("result", {})
        image_path = result.get("filepath")

        if not image_path:
            raise ValueError("Screenshot captured but no file path returned")

        # Read the image data and encode as base64
        import base64
        import os

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            base64_data = base64.b64encode(image_data).decode("utf-8")

            await ctx.info(
                f"Screenshot captured: {image_path} ({len(image_data)} bytes)"
            )

            # Clean up temporary file after reading into memory
            try:
                os.remove(image_path)
                await ctx.info(f"Cleaned up temporary file: {image_path}")
            except Exception as cleanup_error:
                await ctx.error(
                    f"Warning: Failed to cleanup temporary file {image_path}: {cleanup_error}"
                )

            return {
                "type": "image",
                "data": base64_data,
                "mimeType": f"image/{format}",
                "size": len(image_data),
                "dimensions": {
                    "width": result.get("width"),
                    "height": result.get("height"),
                },
            }
        except Exception as read_error:
            # If we can't read the file, try to clean it up anyway
            try:
                os.remove(image_path)
            except:
                pass
            raise read_error

    except Exception as e:
        await ctx.error(f"Failed to capture screenshot: {e}")
        return {"error": str(e)}


@mcp.tool()
async def put_persist_data(key: str, data: Any, ctx: Context) -> Dict[str, Any]:
    """Store data with a key in Blender's persistent storage."""
    await ctx.info(f"Storing data with key: {key}")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "put_persist_data", "params": {"key": key, "data": data}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Failed to store data: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        await ctx.info(f"Data successfully stored with key: {key}")
        return {"success": True, "message": response.get("message", "Data stored")}
    except Exception as e:
        await ctx.error(f"Failed to store data: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_persist_data(key: str, ctx: Context, default: Any = None) -> Dict[str, Any]:
    """Retrieve data by key from Blender's persistent storage."""
    await ctx.info(f"Retrieving data with key: {key}")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "get_persist_data", "params": {"key": key, "default": default}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Failed to retrieve data: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        result = response.get("result", {})
        data = result.get("data")
        found = result.get("found", False)
        
        if found:
            await ctx.info(f"Data retrieved for key: {key}")
        else:
            await ctx.info(f"No data found for key: {key}, returning default")
            
        return {"data": data, "found": found}
    except Exception as e:
        await ctx.error(f"Failed to retrieve data: {e}")
        return {"error": str(e)}


@mcp.tool()
async def remove_persist_data(key: str, ctx: Context) -> Dict[str, Any]:
    """Remove data by key from Blender's persistent storage."""
    await ctx.info(f"Removing data with key: {key}")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {"error": "Blender connection not initialized"}

    try:
        response = await blender_conn.send_command(
            {"type": "remove_persist_data", "params": {"key": key}}
        )

        if response.get("status") == "error":
            await ctx.error(
                f"Failed to remove data: {response.get('message', 'Unknown error')}"
            )
            return {"error": response.get("message", "Unknown error")}

        result = response.get("result", {})
        removed = result.get("removed", False)
        
        if removed:
            await ctx.info(f"Data removed for key: {key}")
        else:
            await ctx.info(f"No data found to remove for key: {key}")
            
        return {"removed": removed}
    except Exception as e:
        await ctx.error(f"Failed to remove data: {e}")
        return {"error": str(e)}


@mcp.tool()
async def check_connection_status(ctx: Context) -> Dict[str, Any]:
    """Check the connection status to Blender's BLD_Remote_MCP service."""
    await ctx.info("Checking connection to Blender...")

    if blender_conn is None:
        await ctx.error("Blender connection not initialized")
        return {
            "status": "error",
            "message": "Blender connection not initialized"
        }

    try:
        response = await blender_conn.send_command(
            {"type": "get_scene_info", "params": {}}
        )

        if response.get("status") == "success":
            await ctx.info("✅ Connected to Blender BLD_Remote_MCP TCP service")
            return {
                "status": "connected",
                "blender_host": blender_conn.blender_host,
                "blender_port": blender_conn.blender_port,
                "service": "BLD_Remote_MCP",
            }
        else:
            await ctx.error(
                f"Connection error: {response.get('message', 'Unknown error')}"
            )
            return {
                "status": "error",
                "message": response.get("message", "Unknown error"),
            }
    except Exception as e:
        await ctx.error(f"Connection failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "suggestion": "Make sure Blender is running with BLD_Remote_MCP addon enabled",
        }


@mcp.resource("blender://status")
async def blender_status() -> Dict[str, Any]:
    """Get the current status of the Blender connection."""
    try:
        if blender_conn is None:
            return {"status": "not_initialized", "message": "Blender connection not initialized"}
        
        if blender_conn.sock:
            return {
                "status": "connected",
                "blender_host": blender_conn.blender_host,
                "blender_port": blender_conn.blender_port,
                "service": "BLD_Remote_MCP",
            }
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
4. **Take Screenshots**: Capture viewport images (GUI mode only)
5. **Check Status**: Monitor connection to Blender
6. **Data Persistence**: Store and retrieve data across commands
   - `put_persist_data(key, data)`: Store data with a key
   - `get_persist_data(key, default)`: Retrieve data by key
   - `remove_persist_data(key)`: Remove data by key

What would you like to do with your Blender scene?"""


def main() -> None:
    """Main entry point for uvx execution."""
    global blender_conn
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle legacy arguments for backward compatibility
    blender_host = args.blender_host
    if args.host is not None:
        blender_host = args.host
        logger.warning("Using legacy --host argument. Please use --blender-host instead.")
    
    # Determine blender port (command line arg takes precedence, then config file, then default)
    blender_port = args.blender_port
    if args.port is not None:
        blender_port = args.port
        logger.warning("Using legacy --port argument. Please use --blender-port instead.")
    if blender_port is None:
        blender_port = get_default_blender_port()
    
    # MCP Server configuration
    mcp_host = args.mcp_host
    mcp_port = args.mcp_port
    
    # Initialize global connection with parsed arguments
    blender_conn = BlenderConnection(blender_host=blender_host, blender_port=blender_port)
    
    # Print connection info to stdout
    logger.info("🚀 Starting Blender Remote MCP Server...")
    logger.info(f"🌐 MCP Server will run on {mcp_host}:{mcp_port}")
    logger.info(f"📡 Will connect to Blender BLD_Remote_MCP TCP service at {blender_host}:{blender_port}")
    logger.info("🔗 Make sure Blender is running with the BLD_Remote_MCP addon enabled")
    
    # Print to stdout for easy visibility
    print(f"Blender Remote MCP Server")
    print(f"MCP Server: {mcp_host}:{mcp_port}")
    print(f"Target Blender TCP service: {blender_host}:{blender_port}")
    
    try:
        # This is the function called when running `uvx blender-remote`
        # Note: FastMCP.run() will use its own server configuration
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
