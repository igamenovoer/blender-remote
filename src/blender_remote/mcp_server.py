"""
Blender Remote MCP Server

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
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP, Context, Image
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection to Blender
blender_connection: Optional[socket.socket] = None
connection_lock = asyncio.Lock()

class BlenderConnectionError(Exception):
    """Raised when connection to Blender fails"""
    pass

def connect_to_blender(host: str = "127.0.0.1", port: int = 6688, timeout: float = 10.0) -> socket.socket:
    """Connect to BLD_Remote_MCP service in Blender"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        logger.info(f"Connected to Blender BLD_Remote_MCP service at {host}:{port}")
        return sock
    except Exception as e:
        logger.error(f"Failed to connect to Blender at {host}:{port}: {e}")
        raise BlenderConnectionError(f"Cannot connect to Blender at {host}:{port}: {e}")

async def send_command_to_blender(command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send a command to Blender and return the response"""
    global blender_connection
    
    async with connection_lock:
        # Ensure we have a connection
        if blender_connection is None:
            try:
                blender_connection = connect_to_blender()
            except BlenderConnectionError as e:
                return {
                    "status": "error",
                    "message": f"Connection failed: {e}"
                }
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            # Send command
            command_json = json.dumps(command)
            blender_connection.sendall(command_json.encode('utf-8'))
            
            # Receive response
            response_data = blender_connection.recv(8192)
            if not response_data:
                raise ConnectionError("Connection closed by Blender")
                
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Command {command_type} executed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error communicating with Blender: {e}")
            # Close and reset connection on error
            if blender_connection:
                try:
                    blender_connection.close()
                except:
                    pass
                blender_connection = None
            
            return {
                "status": "error", 
                "message": f"Communication error with Blender: {e}"
            }

@asynccontextmanager
async def server_lifespan():
    """Manage server lifecycle"""
    logger.info("Starting Blender Remote MCP Server...")
    try:
        # Test initial connection
        await send_command_to_blender("get_scene_info")
        logger.info("Successfully connected to Blender")
    except Exception as e:
        logger.warning(f"Initial connection test failed: {e}")
        logger.info("Server will start anyway - connection will be retried on first request")
    
    yield
    
    # Cleanup
    global blender_connection
    if blender_connection:
        try:
            blender_connection.close()
            logger.info("Closed connection to Blender")
        except:
            pass

# Create FastMCP server instance
mcp = FastMCP(
    "BlenderRemote", 
    description="Remote control Blender through the Model Context Protocol using BLD_Remote_MCP service",
    lifespan=server_lifespan
)

@mcp.tool()
async def get_scene_info(ctx: Context) -> str:
    """Get detailed information about the current Blender scene including objects, materials, and frame settings"""
    response = await send_command_to_blender("get_scene_info")
    
    if response.get("status") == "error":
        return f"Error getting scene info: {response.get('message', 'Unknown error')}"
    
    result = response.get("result", {})
    
    # Format the scene information nicely
    scene_name = result.get("name", "Unknown")
    object_count = result.get("object_count", 0)
    materials_count = result.get("materials_count", 0)
    frame_info = f"Frame {result.get('frame_current', 1)} of {result.get('frame_start', 1)}-{result.get('frame_end', 1)}"
    
    info_lines = [
        f"Scene: {scene_name}",
        f"Objects: {object_count}",
        f"Materials: {materials_count}",
        f"Timeline: {frame_info}",
        ""
    ]
    
    # Add object details if available
    objects = result.get("objects", [])
    if objects:
        info_lines.append("Objects in scene:")
        for obj in objects[:10]:  # Limit to first 10 objects
            obj_name = obj.get("name", "Unknown")
            obj_type = obj.get("type", "Unknown")
            obj_location = obj.get("location", [0, 0, 0])
            obj_visible = obj.get("visible", True)
            
            location_str = f"({obj_location[0]:.2f}, {obj_location[1]:.2f}, {obj_location[2]:.2f})"
            visibility = "visible" if obj_visible else "hidden"
            info_lines.append(f"  - {obj_name} ({obj_type}) at {location_str} [{visibility}]")
        
        if len(objects) > 10:
            info_lines.append(f"  ... and {len(objects) - 10} more objects")
    
    return "\\n".join(info_lines)

@mcp.tool()
async def get_object_info(ctx: Context, object_name: str) -> str:
    """Get detailed information about a specific object in the Blender scene"""
    response = await send_command_to_blender("get_object_info", {"object_name": object_name})
    
    if response.get("status") == "error":
        return f"Error getting object info: {response.get('message', 'Unknown error')}"
    
    result = response.get("result", {})
    
    if not result:
        return f"Object '{object_name}' not found in the scene"
    
    # Format object information
    info_lines = [
        f"Object: {result.get('name', object_name)}",
        f"Type: {result.get('type', 'Unknown')}",
        f"Location: {result.get('location', [0, 0, 0])}",
        f"Rotation: {result.get('rotation_euler', [0, 0, 0])}",
        f"Scale: {result.get('scale', [1, 1, 1])}",
        f"Visible: {result.get('visible', True)}",
    ]
    
    # Add material info if available
    materials = result.get("materials", [])
    if materials:
        info_lines.append(f"Materials: {', '.join(materials)}")
    
    return "\\n".join(info_lines)

@mcp.tool()
async def execute_blender_code(ctx: Context, code: str) -> str:
    """Execute arbitrary Python code in Blender's context. Use this to manipulate scenes, objects, materials, etc."""
    response = await send_command_to_blender("execute_code", {"code": code})
    
    if response.get("status") == "error":
        return f"Error executing code: {response.get('message', 'Unknown error')}"
    
    result = response.get("result", {})
    
    # Return execution result
    if "output" in result:
        return f"Code executed successfully. Output:\\n{result['output']}"
    elif "message" in result:
        return f"Code executed successfully: {result['message']}"
    else:
        return "Code executed successfully"

@mcp.tool()
async def get_viewport_screenshot(ctx: Context, max_size: int = 800, filepath: Optional[str] = None, format: str = "png") -> Image:
    """Capture a screenshot of the current Blender 3D viewport. Note: Only works in GUI mode, not in background mode."""
    response = await send_command_to_blender("get_viewport_screenshot", {
        "max_size": max_size,
        "filepath": filepath,
        "format": format
    })
    
    if response.get("status") == "error":
        error_message = response.get("message", "Unknown error")
        # If it's a background mode error, provide helpful context
        if "background mode" in error_message.lower():
            raise ValueError(f"{error_message}. Consider using rendering instead of viewport screenshots when Blender is running in background mode.")
        else:
            raise ValueError(f"Error capturing screenshot: {error_message}")
    
    result = response.get("result", {})
    
    # Get the image path from response
    image_path = result.get("filepath")
    if not image_path:
        raise ValueError("Screenshot was captured but no file path returned")
    
    # Read the image data and return as Image
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        return Image(data=image_data, media_type=f"image/{format}")
    except Exception as e:
        raise ValueError(f"Error reading screenshot file: {e}")

@mcp.tool()
async def check_connection_status(ctx: Context) -> str:
    """Check the connection status to Blender's BLD_Remote_MCP service"""
    try:
        response = await send_command_to_blender("get_scene_info")
        if response.get("status") == "success":
            return "✅ Connected to Blender BLD_Remote_MCP service (port 6688)"
        else:
            return f"⚠️ Connected but got error: {response.get('message', 'Unknown error')}"
    except Exception as e:
        return f"❌ Connection failed: {e}. Make sure Blender is running with BLD_Remote_MCP addon enabled."

def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Blender Remote MCP Server...")
    logger.info("This server connects to BLD_Remote_MCP service in Blender (port 6688)")
    logger.info("Make sure Blender is running with the BLD_Remote_MCP addon enabled")
    
    try:
        # Run the MCP server using stdio transport
        asyncio.run(stdio_server(mcp))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()