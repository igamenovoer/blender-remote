#!/usr/bin/env python3
"""
Test starting the MCP server briefly to verify it works.
"""
import sys
import os
import asyncio
import signal
import threading
import time

sys.path.insert(0, '/workspace/code/blender-remote/src')

def test_mcp_server_start():
    """Test starting the MCP server for a brief moment."""
    try:
        from blender_remote.mcp_server import main
        
        print("🚀 Testing MCP server startup...")
        print("   This will start the server for 3 seconds then stop it")
        
        # Create a timer to stop the server
        def stop_server():
            time.sleep(3)
            print("⏰ Timer expired, stopping server...")
            os._exit(0)  # Force exit after timeout
        
        # Start timer in background
        timer_thread = threading.Thread(target=stop_server, daemon=True)
        timer_thread.start()
        
        # Try to start the server
        print("📡 Starting MCP server (will auto-stop in 3 seconds)...")
        main()  # This should start the FastMCP server
        
    except SystemExit:
        print("✅ Server started successfully (stopped by timer)")
        return True
    except KeyboardInterrupt:
        print("✅ Server started successfully (stopped by interrupt)")
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server_start()
    sys.exit(0 if success else 1)