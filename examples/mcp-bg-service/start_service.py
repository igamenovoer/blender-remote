#!/usr/bin/env python3
"""
BLD Remote MCP Service Starter

Simple wrapper to start the BLD Remote MCP background service with various options.
Provides a convenient interface for the examples directory.
"""

import os
import sys
import argparse
import subprocess
import signal
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import wait_for_service, check_service_health, print_status

# Default paths
DEFAULT_BLENDER_PATH = "/home/igamenovoer/apps/blender-4.4.3-linux-x64/blender"
DEFAULT_BACKGROUND_SCRIPT = "../../scripts/start_bld_remote_background.py"

def find_blender_executable():
    """Find Blender executable from common locations."""
    # Check environment variable first
    blender_path = os.environ.get('BLENDER_EXEC_PATH')
    if blender_path and os.path.exists(blender_path):
        return blender_path
    
    # Check default path
    if os.path.exists(DEFAULT_BLENDER_PATH):
        return DEFAULT_BLENDER_PATH
    
    # Check system PATH
    import shutil
    blender_path = shutil.which('blender')
    if blender_path:
        return blender_path
    
    return None

def start_background_service(port: int, blender_path: str, wait: bool = True) -> subprocess.Popen:
    """
    Start the BLD Remote MCP background service.
    
    Args:
        port: Port number for the service
        blender_path: Path to Blender executable  
        wait: Whether to wait for service to become ready
        
    Returns:
        Popen object for the background service process
    """
    script_path = Path(__file__).parent / DEFAULT_BACKGROUND_SCRIPT
    
    if not script_path.exists():
        raise FileNotFoundError(f"Background script not found: {script_path}")
    
    if not os.path.exists(blender_path):
        raise FileNotFoundError(f"Blender executable not found: {blender_path}")
    
    print(f"Starting BLD Remote MCP service...")
    print(f"  Port: {port}")
    print(f"  Blender: {blender_path}")
    print(f"  Script: {script_path}")
    
    # Start the background service
    cmd = [
        sys.executable,
        str(script_path),
        "--port", str(port),
        "--blender-path", blender_path
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    print(f"✓ Service process started (PID: {process.pid})")
    
    if wait:
        print("Waiting for service to become ready...")
        if wait_for_service(port=port, timeout=30.0):
            print("✓ Service is ready for connections!")
        else:
            print("✗ Service failed to start within timeout")
            process.terminate()
            return None
    
    return process

def start_gui_service(port: int, blender_path: str) -> subprocess.Popen:
    """
    Start Blender in GUI mode with auto-start enabled.
    
    Args:
        port: Port number for the service
        blender_path: Path to Blender executable
        
    Returns:
        Popen object for the Blender GUI process
    """
    env = os.environ.copy()
    env['BLD_REMOTE_MCP_PORT'] = str(port)
    env['BLD_REMOTE_MCP_START_NOW'] = 'true'
    
    print(f"Starting Blender GUI with BLD Remote MCP...")
    print(f"  Port: {port}")
    print(f"  Blender: {blender_path}")
    
    process = subprocess.Popen([blender_path], env=env)
    
    print(f"✓ Blender GUI started (PID: {process.pid})")
    print("The BLD Remote MCP service should auto-start in ~10 seconds")
    
    return process

def check_existing_service(port: int) -> bool:
    """Check if service is already running on the specified port."""
    health = check_service_health(port=port)
    
    if health["responsive"]:
        print(f"✓ Service already running on port {port}")
        print_status(health)
        return True
    else:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Start BLD Remote MCP service for examples',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start_service.py                    # Start with defaults
  python3 start_service.py --port 9999       # Use custom port
  python3 start_service.py --gui              # Start Blender GUI mode
  python3 start_service.py --check-only      # Just check if running
        """
    )
    
    parser.add_argument('--port', type=int, default=6688,
                        help='Port for MCP service (default: 6688)')
    parser.add_argument('--blender-path', 
                        default=find_blender_executable(),
                        help='Path to Blender executable')
    parser.add_argument('--gui', action='store_true',
                        help='Start Blender in GUI mode instead of background')
    parser.add_argument('--no-wait', action='store_true',
                        help='Don\'t wait for service to become ready')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check if service is running')
    
    args = parser.parse_args()
    
    # Validate Blender path
    if not args.blender_path:
        print("Error: Could not find Blender executable")
        print("Please set BLENDER_EXEC_PATH environment variable or use --blender-path")
        sys.exit(1)
    
    if not os.path.exists(args.blender_path):
        print(f"Error: Blender executable not found: {args.blender_path}")
        sys.exit(1)
    
    # Check if service is already running
    if check_existing_service(args.port):
        if args.check_only:
            sys.exit(0)
        else:
            print("Service is already running. Use a different port or stop the existing service.")
            sys.exit(1)
    
    if args.check_only:
        print(f"No service found on port {args.port}")
        sys.exit(1)
    
    try:
        if args.gui:
            # Start GUI mode
            process = start_gui_service(args.port, args.blender_path)
            wait_time = 15.0
        else:
            # Start background mode
            process = start_background_service(
                args.port, 
                args.blender_path, 
                wait=not args.no_wait
            )
            wait_time = 5.0
        
        if not process:
            print("Failed to start service")
            sys.exit(1)
        
        # Set up signal handling for clean shutdown
        def signal_handler(signum, frame):
            print(f"\\nReceived signal {signum}, shutting down...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing process...")
                process.kill()
                process.wait()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print(f"\\nService is starting...")
        print(f"  • Port: {args.port}")
        print(f"  • Mode: {'GUI' if args.gui else 'Background'}")
        print(f"  • PID: {process.pid}")
        print("\\nPress Ctrl+C to stop the service")
        
        if args.gui:
            print(f"\\nWaiting {wait_time}s for GUI startup...")
            time.sleep(wait_time)
            
            if wait_for_service(port=args.port, timeout=20.0):
                print("\\n✓ GUI service is ready!")
            else:
                print("\\n⚠️ Service may still be starting...")
        
        # Monitor the process
        try:
            if args.gui:
                # For GUI mode, just wait for process to end
                process.wait()
            else:
                # For background mode, monitor output
                for line in process.stdout:
                    print(line.rstrip())
        except KeyboardInterrupt:
            print("\\nInterrupted by user")
        
        # Clean shutdown
        return_code = process.poll()
        if return_code is None:
            print("Terminating process...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing process...")
                process.kill()
                process.wait()
        
        print("Service stopped")
        
    except Exception as e:
        print(f"Error starting service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()