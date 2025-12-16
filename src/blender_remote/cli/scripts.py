"""Embedded scripts used by the blender-remote CLI."""

KEEPALIVE_SCRIPT = """
# Keep Blender running in background mode
import time
import signal
import sys
import threading
import platform
from typing import Any

# Global flag to control the keep-alive loop
_keep_running = True


def signal_handler(signum: int, frame: Any) -> None:
    global _keep_running
    print(f"Received signal {signum}, shutting down...")
    _keep_running = False

    # Try to gracefully shutdown the MCP service
    try:
        import bld_remote
        if bld_remote.is_mcp_service_up():
            bld_remote.stop_mcp_service()
            print("MCP service stopped")
    except Exception as e:
        print(f"Error stopping MCP service: {e}")

    # Allow a moment for cleanup
    time.sleep(0.5)
    sys.exit(0)

# Install signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

# SIGTERM is not available on Windows
if platform.system() != "Windows":
    signal.signal(signal.SIGTERM, signal_handler)  # Termination

print("Blender running in background mode. Press Ctrl+C to exit.")
print("MCP service should be starting on the configured port...")

# Keep the main thread alive with simple sleep loop (sync version)
# This prevents Blender from exiting after the script finishes
try:
    # Give the MCP service time to start up
    print("Waiting for MCP service to fully initialize...")
    time.sleep(2)

    print("[SUCCESS] Starting main background loop...")

    # Import BLD Remote module for status checking
    import bld_remote

    # Verify service started successfully
    status = bld_remote.get_status()
    if status.get('running'):
        print(f"[SUCCESS] MCP service is running on port {status.get('port')}")
    else:
        print("[WARN] Warning: MCP service may not have started properly")

    # Main keep-alive loop with background mode command processing
    while _keep_running:
        # Process any queued commands in background mode
        try:
            import bld_remote
            if bld_remote.is_background_mode():
                # Call step() to process queued commands in background mode
                bld_remote.step()
        except ImportError:
            # bld_remote module not available, skip step processing
            pass
        except Exception as e:
            print(f"Warning: Error in background step processing: {e}")

        # Simple keep-alive loop for synchronous threading-based server
        # The server runs in its own daemon threads, we just need to prevent
        # the main thread from exiting
        time.sleep(0.05)  # 50ms sleep for responsive signal handling

except KeyboardInterrupt:
    print("Interrupted by user, shutting down...")
    _keep_running = False

print("Background mode keep-alive loop finished, Blender will exit.")
"""

