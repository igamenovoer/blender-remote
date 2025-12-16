from __future__ import annotations

import os
import subprocess
import tempfile

import click

from ..addon import build_addon_install_script, get_debug_addon_zip_path
from ..config import BlenderRemoteConfig


@click.group()
def debug() -> None:
    """Debug tools for testing code execution patterns"""


@debug.command()
def debug_install() -> None:
    """Install simple-tcp-executor debug addon to Blender"""
    click.echo("[DEBUG] Installing simple-tcp-executor debug addon...")

    # Load config
    config = BlenderRemoteConfig()
    blender_config = config.get("blender")

    if not blender_config:
        raise click.ClickException("Blender configuration not found. Run 'init' first.")

    blender_path = blender_config.get("exec_path")

    if not blender_path:
        raise click.ClickException("Blender executable path not found in config")

    # Get debug addon zip path
    debug_addon_zip = get_debug_addon_zip_path()

    click.echo(f"[ADDON] Using debug addon: {debug_addon_zip}")

    # Create Python script for debug addon installation
    # Use as_posix() to ensure forward slashes on all platforms
    debug_addon_zip_posix = debug_addon_zip.as_posix()
    install_script = build_addon_install_script(
        debug_addon_zip_posix, "simple-tcp-executor"
    )

    # Create temporary script file
    temp_script = None
    try:
        # Create temporary file
        temp_fd, temp_script = tempfile.mkstemp(suffix=".py", text=True)
        with os.fdopen(temp_fd, "w") as f:
            f.write(install_script)

        # Install addon using Blender CLI with Python script
        result = subprocess.run(
            [blender_path, "--background", "--python", temp_script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            click.echo("[SUCCESS] Debug addon installed successfully!")
            click.echo(
                f"[LOCATION] Addon location: {blender_config.get('plugin_dir')}/simple-tcp-executor"
            )
        else:
            click.echo("[ERROR] Installation failed!")
            click.echo(f"Error: {result.stderr}")
            click.echo(f"Output: {result.stdout}")
            raise click.ClickException("Debug addon installation failed")

    except subprocess.TimeoutExpired as exc:
        raise click.ClickException("Installation timeout") from exc
    except Exception as e:
        raise click.ClickException(f"Installation error: {e}") from e
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass  # Ignore cleanup errors


@debug.command(name="start")
@click.option("--background", is_flag=True, help="Start Blender in background mode")
@click.option(
    "--port",
    type=int,
    help="TCP port for debug server (default: 7777 or BLD_DEBUG_TCP_PORT env var)",
)
def debug_start(background: bool, port: int | None) -> int:
    """Start Blender with simple-tcp-executor debug addon"""

    # Load config
    config = BlenderRemoteConfig()
    blender_config = config.get("blender")

    if not blender_config:
        raise click.ClickException("Blender configuration not found. Run 'init' first.")

    blender_path = blender_config.get("exec_path")

    if not blender_path:
        raise click.ClickException("Blender executable path not found in config")

    # Determine port
    debug_port = port or int(os.environ.get("BLD_DEBUG_TCP_PORT", 7777))

    # Prepare startup code
    startup_code = f"""
# Set debug TCP port
import os
os.environ['BLD_DEBUG_TCP_PORT'] = '{debug_port}'

# Enable the debug addon
import bpy
try:
    bpy.ops.preferences.addon_enable(module='simple-tcp-executor')
    print(f"[SUCCESS] Simple TCP Executor debug addon enabled on port {debug_port}")
except Exception as e:
    print(f"[ERROR] Failed to enable debug addon: {{e}}")
    print("Make sure the addon is installed first using 'debug install'")
"""

    if background:
        startup_code += """
# Keep Blender running in background mode
import time
import signal
import sys
import platform

# Global flag to control the keep-alive loop
_keep_running = True

def signal_handler(signum, frame):
    global _keep_running
    print(f"Received signal {signum}, shutting down...")
    _keep_running = False

    # Allow a moment for cleanup
    time.sleep(0.5)
    sys.exit(0)

# Install signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

# SIGTERM is not available on Windows
if platform.system() != "Windows":
    signal.signal(signal.SIGTERM, signal_handler)  # Termination

print("Blender running in background mode with debug TCP server. Press Ctrl+C to exit.")
print(f"Debug TCP server should be listening on port {os.environ.get('BLD_DEBUG_TCP_PORT', 7777)}")

# Keep the main thread alive with manual step() processing
try:
    print("[SUCCESS] Starting debug background loop...")

    # Write to debug log directly
    with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
        f.write("DEBUG: Entering main loop section\\n")
        f.flush()

    # Get the addon's step function using the registered API module
    import bpy
    step_processor = None
    try:
        # Import the registered API module
        import simple_tcp_executor
        step_processor = simple_tcp_executor.step
        print("DEBUG: Found step processor function via registered API module")
        with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
            f.write("DEBUG: Found step processor function via registered API module\\n")
            f.flush()

        # Test if the API is working
        is_running = simple_tcp_executor.is_running()
        print(f"DEBUG: TCP executor running status: {is_running}")
        with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
            f.write(f"DEBUG: TCP executor running status: {is_running}\\n")
            f.flush()

    except ImportError as e:
        print(f"DEBUG: Could not import simple_tcp_executor API: {e}")
        with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
            f.write(f"DEBUG: Could not import simple_tcp_executor API: {e}\\n")
            f.flush()
    except Exception as e:
        print(f"DEBUG: Error accessing TCP executor API: {e}")
        with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
            f.write(f"DEBUG: Error accessing TCP executor API: {e}\\n")
            f.flush()

    # Main keep-alive loop with manual step() processing
    loop_count = 0
    while _keep_running:
        loop_count += 1

        # Log every 100 iterations to show the loop is running
        if loop_count % 100 == 0:
            with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
                f.write(f"DEBUG: Main loop iteration {loop_count}\\n")
                f.flush()

        # Manually call the step function to process the queue
        if step_processor:
            try:
                step_processor()
            except Exception as e:
                print(f"DEBUG: Error in step processor: {e}")
                with open(os.path.join(tempfile.gettempdir(), 'blender_debug.log'), 'a') as f:
                    f.write(f"DEBUG: Error in step processor: {e}\\n")
                    f.flush()

        time.sleep(0.05)  # 50ms sleep for responsive signal handling

except KeyboardInterrupt:
    print("Interrupted by user, shutting down...")
    _keep_running = False

print("Debug background mode finished, Blender will exit.")
"""

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(startup_code)
        temp_script = temp_file.name

    try:
        # Build command
        cmd = [blender_path]

        if background:
            cmd.append("--background")

        cmd.extend(["--python", temp_script])

        click.echo(f"[DEBUG] Starting Blender with debug TCP server on port {debug_port}...")

        if background:
            click.echo("[MODE] Background mode: Blender will run headless")
        else:
            click.echo("[MODE] GUI mode: Blender window will open")

        # Set up environment variables for debug mode
        blender_env = os.environ.copy()
        blender_env["BLD_REMOTE_MCP_START_NOW"] = "false"  # Debug mode doesn't auto-start MCP
        blender_env["BLD_REMOTE_LOG_LEVEL"] = "DEBUG"

        # Execute Blender
        result = subprocess.run(cmd, timeout=None, env=blender_env)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass

