"""
Enhanced command-line interface for blender-remote.

This CLI provides additional commands beyond the main MCP server functionality.
The main entry point (uvx blender-remote) starts the MCP server.
"""

import sys
import argparse
import json
import socket
from typing import Optional

def connect_and_send_command(command_type: str, params: dict = None, host: str = "127.0.0.1", port: int = 6688, timeout: float = 10.0) -> dict:
    """Connect to BLD_Remote_MCP and send a command"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        # Send command
        command_json = json.dumps(command)
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {e}"
        }

def cmd_status():
    """Check connection status to Blender"""
    print("🔍 Checking connection to Blender BLD_Remote_MCP service...")
    
    response = connect_and_send_command("get_scene_info")
    
    if response.get("status") == "success":
        print("✅ Connected to Blender BLD_Remote_MCP service (port 6688)")
        scene_info = response.get("result", {})
        scene_name = scene_info.get("name", "Unknown")
        object_count = scene_info.get("object_count", 0)
        print(f"   Scene: {scene_name}")
        print(f"   Objects: {object_count}")
    else:
        error_msg = response.get("message", "Unknown error")
        print(f"❌ Connection failed: {error_msg}")
        print("   Make sure Blender is running with BLD_Remote_MCP addon enabled")

def cmd_exec(code: str):
    """Execute Python code in Blender"""
    print(f"🚀 Executing code in Blender...")
    print(f"Code: {code}")
    
    response = connect_and_send_command("execute_code", {"code": code})
    
    if response.get("status") == "success":
        result = response.get("result", {})
        print("✅ Code executed successfully")
        if "output" in result:
            print(f"Output: {result['output']}")
        elif "message" in result:
            print(f"Result: {result['message']}")
    else:
        error_msg = response.get("message", "Unknown error")
        print(f"❌ Execution failed: {error_msg}")

def cmd_scene():
    """Get scene information"""
    print("📋 Getting scene information...")
    
    response = connect_and_send_command("get_scene_info")
    
    if response.get("status") == "success":
        result = response.get("result", {})
        
        print("✅ Scene Information:")
        print(f"   Scene: {result.get('name', 'Unknown')}")
        print(f"   Objects: {result.get('object_count', 0)}")
        print(f"   Materials: {result.get('materials_count', 0)}")
        print(f"   Frame: {result.get('frame_current', 1)} of {result.get('frame_start', 1)}-{result.get('frame_end', 1)}")
        
        objects = result.get("objects", [])
        if objects:
            print("   Objects in scene:")
            for obj in objects[:5]:  # Show first 5 objects
                obj_name = obj.get("name", "Unknown")
                obj_type = obj.get("type", "Unknown")
                obj_location = obj.get("location", [0, 0, 0])
                print(f"     - {obj_name} ({obj_type}) at ({obj_location[0]:.2f}, {obj_location[1]:.2f}, {obj_location[2]:.2f})")
            
            if len(objects) > 5:
                print(f"     ... and {len(objects) - 5} more objects")
    else:
        error_msg = response.get("message", "Unknown error")
        print(f"❌ Failed to get scene info: {error_msg}")

def cmd_screenshot(output: str = "screenshot.png", max_size: int = 800):
    """Capture viewport screenshot"""
    print(f"📸 Capturing screenshot...")
    
    response = connect_and_send_command("get_viewport_screenshot", {
        "filepath": output,
        "max_size": max_size,
        "format": "png"
    })
    
    if response.get("status") == "success":
        result = response.get("result", {})
        filepath = result.get("filepath", output)
        print(f"✅ Screenshot saved to: {filepath}")
    else:
        error_msg = response.get("message", "Unknown error")
        print(f"❌ Screenshot failed: {error_msg}")
        if "background mode" in error_msg.lower():
            print("   Note: Screenshots don't work in background mode. Use rendering instead.")

def main():
    """Enhanced CLI entry point for blender-remote tools"""
    parser = argparse.ArgumentParser(
        description="Enhanced CLI tools for blender-remote",
        prog="blender-remote-cli"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
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
    
    # Scene info command
    scene_parser = subparsers.add_parser(
        "scene",
        help="Get current scene information"
    )
    
    # Screenshot command
    screenshot_parser = subparsers.add_parser(
        "screenshot",
        help="Capture viewport screenshot (GUI mode only)"
    )
    screenshot_parser.add_argument(
        "--output",
        "-o",
        default="screenshot.png",
        help="Output file path (default: screenshot.png)"
    )
    screenshot_parser.add_argument(
        "--max-size",
        type=int,
        default=800,
        help="Maximum image size (default: 800)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "status":
            cmd_status()
        elif args.command == "exec":
            cmd_exec(args.code)
        elif args.command == "scene":
            cmd_scene()
        elif args.command == "screenshot":
            cmd_screenshot(args.output, args.max_size)
        else:
            print(f"Unknown command: {args.command}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())