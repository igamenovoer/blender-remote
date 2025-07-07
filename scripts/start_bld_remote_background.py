#!/usr/bin/env python3
"""
BLD Remote MCP Background Mode Script

This script starts Blender in background mode and manages the BLD Remote MCP server
using the proven blender-echo-plugin pattern with external loop management.

Usage:
    python start_bld_remote_background.py [--port PORT] [--blender-path PATH]

Environment Variables:
    BLD_REMOTE_MCP_PORT: Server port (default: 6688)
    BLD_REMOTE_MCP_START_NOW: Auto-start flag (default: true)
    BLENDER_EXEC_PATH: Path to Blender executable
"""

import os
import sys
import time
import argparse
import subprocess
import tempfile
import signal
import atexit

# Default Blender path
DEFAULT_BLENDER_PATH = "/home/igamenovoer/apps/blender-4.4.3-linux-x64/blender"

def create_background_script(port):
    """Create a Python script to run inside Blender for background mode"""
    script_content = f'''
import bpy
import os
import sys
import time

# Set environment variables for BLD Remote MCP
os.environ['BLD_REMOTE_MCP_PORT'] = '{port}'
os.environ['BLD_REMOTE_MCP_START_NOW'] = 'true'

print(f"[BLD Remote Background] Starting on port {port}")

try:
    # Enable the BLD Remote MCP addon
    bpy.ops.preferences.addon_enable(module='bld_remote_mcp')
    print("[BLD Remote Background] Addon enabled")
    
    # Import and start the server
    import bld_remote
    
    # Wait a moment for initialization
    time.sleep(1)
    
    # Check status and start if needed
    status = bld_remote.get_status()
    print(f"[BLD Remote Background] Initial status: {{status}}")
    
    if not status['running']:
        print("[BLD Remote Background] Starting MCP service manually")
        bld_remote.start_mcp_service()
        
        # Wait for server to start
        time.sleep(2)
        status = bld_remote.get_status()
        print(f"[BLD Remote Background] Status after manual start: {{status}}")
    
    # Start the async loop operator to process asyncio events
    import bld_remote_mcp.async_loop as async_loop
    async_loop.ensure_async_loop()
    print("[BLD Remote Background] Async loop operator started")
    
    # Keep Blender alive by continuously kicking the async loop
    print("[BLD Remote Background] Starting background event loop...")
    print(f"[BLD Remote Background] Server ready on port {port}")
    print("[BLD Remote Background] Send 'quit_blender' command to shutdown")
    
    # Main background loop - keeps Blender alive and processes asyncio events
    while True:
        try:
            # Kick the async loop to process events
            stop_loop = async_loop.kick_async_loop()
            
            if stop_loop:
                print("[BLD Remote Background] Async loop signaled to stop")
                break
                
            # Small delay to prevent CPU spinning
            time.sleep(0.01)
            
        except SystemExit:
            print("[BLD Remote Background] SystemExit received - shutting down")
            break
        except KeyboardInterrupt:
            print("[BLD Remote Background] KeyboardInterrupt received - shutting down")
            break
        except Exception as e:
            print(f"[BLD Remote Background] Error in background loop: {{e}}")
            # Continue running despite errors
            time.sleep(0.1)

except Exception as e:
    print(f"[BLD Remote Background] Failed to start: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[BLD Remote Background] Background script completed")
'''
    return script_content

def cleanup_handler(blender_process):
    """Cleanup function to ensure Blender process is terminated"""
    try:
        if blender_process and blender_process.poll() is None:
            print("\\n[BLD Remote Background] Terminating Blender process...")
            blender_process.terminate()
            
            # Wait a moment for graceful shutdown
            try:
                blender_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[BLD Remote Background] Force killing Blender process...")
                blender_process.kill()
                blender_process.wait()
                
    except Exception as e:
        print(f"[BLD Remote Background] Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description='Start BLD Remote MCP in background mode')
    parser.add_argument('--port', type=int, default=int(os.environ.get('BLD_REMOTE_MCP_PORT', 6688)),
                        help='Port for MCP server (default: 6688)')
    parser.add_argument('--blender-path', default=os.environ.get('BLENDER_EXEC_PATH', DEFAULT_BLENDER_PATH),
                        help='Path to Blender executable')
    
    args = parser.parse_args()
    
    print(f"[BLD Remote Background] Starting BLD Remote MCP on port {args.port}")
    print(f"[BLD Remote Background] Using Blender: {args.blender_path}")
    
    # Check if Blender exists
    if not os.path.exists(args.blender_path):
        print(f"Error: Blender not found at {args.blender_path}")
        print("Please set BLENDER_EXEC_PATH environment variable or use --blender-path")
        sys.exit(1)
    
    # Create temporary script file
    script_content = create_background_script(args.port)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    
    try:
        # Start Blender in background mode with our script
        print(f"[BLD Remote Background] Starting Blender with background script...")
        
        blender_cmd = [
            args.blender_path,
            '--background',
            '--python',
            script_path
        ]
        
        # Start Blender process
        blender_process = subprocess.Popen(
            blender_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Set up cleanup handler
        def signal_handler(signum, frame):
            print(f"\\n[BLD Remote Background] Received signal {signum}")
            cleanup_handler(blender_process)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(lambda: cleanup_handler(blender_process))
        
        print(f"[BLD Remote Background] Blender process started (PID: {blender_process.pid})")
        print(f"[BLD Remote Background] MCP server should be available on port {args.port}")
        print("[BLD Remote Background] Press Ctrl+C to stop")
        
        # Monitor Blender output
        try:
            for line in blender_process.stdout:
                print(line.rstrip())
        except KeyboardInterrupt:
            print("\\n[BLD Remote Background] Interrupted by user")
        
        # Wait for Blender to finish
        return_code = blender_process.wait()
        print(f"[BLD Remote Background] Blender process exited with code {return_code}")
        
    finally:
        # Clean up temporary script
        try:
            os.unlink(script_path)
        except:
            pass

if __name__ == '__main__':
    main()