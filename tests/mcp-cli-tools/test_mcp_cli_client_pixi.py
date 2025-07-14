#!/usr/bin/env python3
"""
Test MCP CLI client using pixi environment and the official MCP Python SDK
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def interact_with_blender_mcp_pixi():
    """
    Test the blender-mcp server using pixi environment and MCP client SDK
    """
    print("=== Testing blender-mcp server with MCP CLI client (Pixi) ===")
    
    # Configure server parameters using pixi
    server_script_path = os.path.abspath("context/refcode/blender-mcp/src/blender_mcp/server.py")
    
    # Use pixi run python to ensure we're in the correct environment
    server_params = StdioServerParameters(
        command="pixi",
        args=["run", "python", server_script_path],
        env=None,
    )
    
    try:
        print(f"Connecting to server via pixi: {server_script_path}")
        
        # Connect to server using stdio transport
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                print("Initializing MCP session...")
                await session.initialize()
                print("✅ Session initialized successfully")
                
                # List available tools
                print("\n1. Listing available tools...")
                tools = await session.list_tools()
                print(f"Available tools ({len(tools.tools)}):")
                for i, tool in enumerate(tools.tools[:5]):  # Show first 5 tools
                    print(f"  {i+1}. {tool.name}: {tool.description[:60]}...")
                if len(tools.tools) > 5:
                    print(f"  ... and {len(tools.tools) - 5} more tools")
                
                # Call get_scene_info tool
                print("\n2. Calling get_scene_info tool...")
                scene_result = await session.call_tool("get_scene_info", {})
                if scene_result.content:
                    content = scene_result.content[0].text if scene_result.content[0].type == 'text' else str(scene_result.content[0])
                    print(f"Scene info: {content[:150]}...")
                
                # Execute Blender code
                print("\n3. Executing Blender code...")
                code = "import bpy; print(f'Pixi test - Scene: {bpy.context.scene.name}, Objects: {len(bpy.context.scene.objects)}')"
                code_result = await session.call_tool("execute_code", {
                    "code": code
                })
                if code_result.content:
                    content = code_result.content[0].text if code_result.content[0].type == 'text' else str(code_result.content[0])
                    print(f"Code execution result: {content}")
                
                print("\n✅ All pixi MCP CLI tests completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error during pixi MCP CLI testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await interact_with_blender_mcp_pixi()
    print(f"\n=== Pixi MCP CLI Test Result: {'SUCCESS' if success else 'FAILED'} ===")

if __name__ == "__main__":
    asyncio.run(main())