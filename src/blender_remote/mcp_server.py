"""
FastMCP server implementation for Blender Remote.

This module provides a Model Context Protocol (MCP) server that connects to
the BLD_Remote_MCP service running inside Blender. This allows LLM IDEs to
control Blender through the MCP protocol.

Usage:
    uvx blender-remote

This will start an MCP server that communicates with Blender's BLD_Remote_MCP service.
"""

import asyncio
import json
import logging
import socket
import sys
import time
from typing import Any, Dict, Optional, cast

from fastmcp import FastMCP, Context
from fastmcp.utilities.types import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp: FastMCP = FastMCP("Blender Remote MCP")


class BlenderConnection:
    """Handle connection to Blender TCP server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 6688):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None

    async def connect(self) -> bool:
        """Connect to Blender addon."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(
                f"Connected to Blender BLD_Remote_MCP at {self.host}:{self.port}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {e}")
            self.sock = None
            return False

    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to Blender and get response."""
        if not self.sock:
            if not await self.connect():
                raise ConnectionError(
                    "Cannot connect to Blender BLD_Remote_MCP service"
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


# Global connection instance
blender_conn = BlenderConnection()


@mcp.tool()
async def get_scene_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the current Blender scene."""
    await ctx.info("Getting scene information from Blender...")

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
async def check_connection_status(ctx: Context) -> Dict[str, Any]:
    """Check the connection status to Blender's BLD_Remote_MCP service."""
    await ctx.info("Checking connection to Blender...")

    try:
        response = await blender_conn.send_command(
            {"type": "get_scene_info", "params": {}}
        )

        if response.get("status") == "success":
            await ctx.info("✅ Connected to Blender BLD_Remote_MCP service")
            return {
                "status": "connected",
                "host": blender_conn.host,
                "port": blender_conn.port,
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
        if blender_conn.sock:
            return {
                "status": "connected",
                "host": blender_conn.host,
                "port": blender_conn.port,
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

What would you like to do with your Blender scene?"""


def main() -> None:
    """Main entry point for uvx execution."""
    logger.info("🚀 Starting Blender Remote MCP Server...")
    logger.info(
        "📡 This server connects to BLD_Remote_MCP service in Blender (port 6688)"
    )
    logger.info("🔗 Make sure Blender is running with the BLD_Remote_MCP addon enabled")

    try:
        # This is the function called when running `uvx blender-remote`
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
