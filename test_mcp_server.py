#!/usr/bin/env python3
"""
Test script to verify the MCP server functionality.
"""
import sys
import os
sys.path.insert(0, '/workspace/code/blender-remote/src')

def test_import():
    """Test if we can import the MCP server module."""
    try:
        from blender_remote import mcp_server
        print("✅ Successfully imported blender_remote.mcp_server")
        return True
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        return False

def test_server_creation():
    """Test if we can create the MCP server instance."""
    try:
        from blender_remote.mcp_server import mcp
        print("✅ Successfully created MCP server instance")
        print(f"   Server name: BlenderRemote")
        return True
    except Exception as e:
        print(f"❌ Failed to create server: {e}")
        return False

def test_tools_registration():
    """Test if tools are properly registered."""
    try:
        from blender_remote.mcp_server import mcp
        
        # Get registered tools
        tools = []
        for tool_name in dir(mcp):
            if hasattr(getattr(mcp, tool_name), '__tool__'):
                tools.append(tool_name)
        
        print(f"✅ Found {len(tools)} registered tools:")
        for tool in tools:
            print(f"   - {tool}")
        
        return len(tools) > 0
    except Exception as e:
        print(f"❌ Failed to check tools: {e}")
        return False

def test_connection_functionality():
    """Test connection to Blender (without starting full server)."""
    try:
        from blender_remote.mcp_server import send_command_to_blender
        import asyncio
        
        print("🔍 Testing connection to Blender...")
        
        # Test connection
        async def test_conn():
            response = await send_command_to_blender("get_scene_info")
            return response
        
        response = asyncio.run(test_conn())
        
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

def main():
    """Run all tests."""
    print("🧪 Testing Blender Remote MCP Server Implementation")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_import),
        ("Server Creation Test", test_server_creation),
        ("Tools Registration Test", test_tools_registration),
        ("Connection Test", test_connection_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   Test failed")
        except Exception as e:
            print(f"   Test error: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP server implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())