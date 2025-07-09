#!/usr/bin/env python3
"""
Test script to verify the FastMCP server functionality.
"""
import sys
import os
import asyncio
sys.path.insert(0, '/workspace/code/blender-remote/src')

async def test_blender_connection():
    """Test if we can connect to Blender through the FastMCP server."""
    try:
        from blender_remote.mcp_server import blender_conn
        
        print("🔍 Testing connection to BLD_Remote_MCP service...")
        
        # Test connection
        response = await blender_conn.send_command({
            "type": "get_scene_info",
            "params": {}
        })
        
        if response.get("status") == "success":
            print("✅ Successfully connected to BLD_Remote_MCP service")
            scene_info = response.get("result", {})
            print(f"   Scene: {scene_info.get('name', 'Unknown')}")
            print(f"   Objects: {scene_info.get('object_count', 0)}")
            return True
        else:
            print(f"❌ Connection test failed: {response.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def test_fastmcp_imports():
    """Test if FastMCP imports work correctly."""
    try:
        from fastmcp import FastMCP, Context
        from fastmcp.utilities.types import Image
        print("✅ FastMCP imports successful")
        return True
    except Exception as e:
        print(f"❌ FastMCP import error: {e}")
        return False

def test_server_creation():
    """Test if the FastMCP server can be created."""
    try:
        from blender_remote.mcp_server import mcp
        print("✅ FastMCP server instance created successfully")
        print(f"   Server name: {mcp.name}")
        return True
    except Exception as e:
        print(f"❌ Server creation error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing FastMCP Blender Remote Server")
    print("=" * 50)
    
    tests = [
        ("FastMCP Imports", test_fastmcp_imports),
        ("Server Creation", test_server_creation),
        ("Blender Connection", test_blender_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"   Test error: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FastMCP server is ready for VSCode integration.")
        print("\n🚀 To use in VSCode:")
        print("   1. Make sure Blender is running with BLD_Remote_MCP addon")
        print("   2. Use the configuration in .vscode/settings.json")
        print("   3. Your MCP server will be available as 'blender-remote-dev'")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))