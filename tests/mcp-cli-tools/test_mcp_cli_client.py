#!/usr/bin/env python3
"""
Test MCP CLI client using the official MCP Python SDK
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def interact_with_blender_mcp():
    """
    Test the blender-mcp server using the official MCP client SDK
    """
    print("=== Testing blender-mcp server with MCP CLI client ===")
    
    # Configure server parameters
    server_script_path = os.path.abspath("context/refcode/blender-mcp/src/blender_mcp/server.py")
    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
        env=None,
    )
    
    try:
        print(f"Connecting to server: {server_script_path}")
        
        # Connect to server using stdio transport
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                print("Initializing MCP session...")
                await session.initialize()
                print("[PASS] Session initialized successfully")
                
                # List available tools
                print("\n1. Listing available tools...")
                tools = await session.list_tools()
                print(f"Available tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Call get_scene_info tool
                print("\n2. Calling get_scene_info tool...")
                scene_result = await session.call_tool("get_scene_info", {})
                print(f"Scene info result: {scene_result}")
                
                # Execute Blender code
                print("\n3. Executing Blender code...")
                code = "import bpy; print(f'Scene: {bpy.context.scene.name}, Objects: {len(bpy.context.scene.objects)}')"
                code_result = await session.call_tool("execute_code", {
                    "code": code
                })
                print(f"Code execution result: {code_result}")
                
                # Test another tool - get viewport screenshot
                print("\n4. Testing get_viewport_screenshot...")
                try:
                    screenshot_result = await session.call_tool("get_viewport_screenshot", {})
                    print(f"Screenshot result: {str(screenshot_result)[:200]}...")
                except Exception as e:
                    print(f"Screenshot failed (expected in headless): {e}")
                
                print("\n[PASS] All MCP CLI tests completed successfully!")
                return True
                
    except Exception as e:
        print(f"[FAIL] Error during MCP CLI testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await interact_with_blender_mcp()
    print(f"\n=== MCP CLI Test Result: {'SUCCESS' if success else 'FAILED'} ===")

if __name__ == "__main__":
    asyncio.run(main())