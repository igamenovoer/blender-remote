"""Enhanced command-line interface for blender-remote using click.

This CLI provides comprehensive blender-remote management functionality.
The main entry point (uvx blender-remote) starts the MCP server.

Platform Support:
- Windows: Full support with automatic Blender path detection
- Linux: Full support with automatic Blender path detection  
- macOS: Full support with automatic Blender path detection
- Cross-platform compatibility maintained throughout
"""

import base64
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import click
import platformdirs
from omegaconf import DictConfig, OmegaConf

# Cross-platform configuration directory using platformdirs
CONFIG_DIR = Path(platformdirs.user_config_dir(appname="blender-remote", appauthor="blender-remote"))
CONFIG_FILE = CONFIG_DIR / "bld-remote-config.yaml"

# Configuration constants that align with MCPServerConfig
# NOTE: These values must stay in sync with MCPServerConfig in mcp_server.py
DEFAULT_PORT = 6688  # Should match MCPServerConfig.FALLBACK_BLENDER_PORT
SOCKET_TIMEOUT_SECONDS = 60.0  # Should match MCPServerConfig.SOCKET_TIMEOUT_SECONDS
SOCKET_RECV_CHUNK_SIZE = 131072  # Should match MCPServerConfig.SOCKET_RECV_CHUNK_SIZE (128KB)
SOCKET_MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # Should match MCPServerConfig.SOCKET_MAX_RESPONSE_SIZE (10MB)


class BlenderRemoteConfig:
    """OmegaConf-based configuration manager for blender-remote"""

    def __init__(self) -> None:
        self.config_path = CONFIG_FILE
        self.config: DictConfig | None = None

    def load(self) -> DictConfig:
        """Load configuration from file"""
        if not self.config_path.exists():
            raise click.ClickException(
                f"Configuration file not found: {self.config_path}\nRun 'blender-remote-cli init [blender_path]' first"
            )

        self.config = OmegaConf.load(self.config_path)
        return self.config

    def save(self, config: dict[str, Any] | DictConfig) -> None:
        """Save configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Convert dict to DictConfig if needed
        if isinstance(config, dict):
            config = OmegaConf.create(config)

        # Save to file
        OmegaConf.save(config, self.config_path)
        self.config = config

    def get(self, key: str) -> Any:
        """Get configuration value using dot notation"""
        if self.config is None:
            self.load()

        # Use OmegaConf.select for safe access with None default
        return OmegaConf.select(self.config, key)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if self.config is None:
            self.load()

        # Use OmegaConf.update for dot notation setting
        OmegaConf.update(self.config, key, value, merge=True)

        # Save the updated configuration
        OmegaConf.save(self.config, self.config_path)


def detect_blender_info(blender_path: str | Path) -> dict[str, Any]:
    """Detect Blender version and paths"""
    blender_path_obj = Path(blender_path)

    if not blender_path_obj.exists():
        raise click.ClickException(f"Blender executable not found: {blender_path_obj}")

    # Get version
    try:
        result = subprocess.run(
            [str(blender_path_obj), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        version_match = re.search(r"Blender (\d+\.\d+\.\d+)", result.stdout)
        if version_match:
            version = version_match.group(1)
            major, minor, _ = map(int, version.split("."))

            if major < 4:
                raise click.ClickException(
                    f"Blender version {version} is not supported. Please use Blender 4.0 or higher."
                )
        else:
            raise click.ClickException("Could not detect Blender version")

    except subprocess.TimeoutExpired:
        raise click.ClickException("Timeout while detecting Blender version")
    except Exception as e:
        raise click.ClickException(f"Error detecting Blender version: {e}")

    # Detect root directory
    root_dir = blender_path_obj.parent

    # Detect plugin directory
    plugin_dir = None

    # Platform-specific addon directory patterns
    if platform.system() == "Windows":
        # Windows addon paths - use platformdirs for APPDATA
        appdata = Path(platformdirs.user_data_dir(appname="", appauthor="")).parent  # Gets AppData/Roaming

        # Try user-specific addon directory first
        blender_config = appdata / "Blender Foundation" / "Blender" / f"{major}.{minor}" / "scripts" / "addons"
        if blender_config.exists():
            plugin_dir = blender_config

        if not plugin_dir:
            # Try system-wide installation in Program Files
            system_addons = root_dir / f"{major}.{minor}" / "scripts" / "addons"
            if system_addons.exists():
                plugin_dir = system_addons
    elif platform.system() == "darwin":
        # macOS addon paths
        blender_config = Path.home() / "Library" / "Application Support" / "Blender" / f"{major}.{minor}" / "scripts" / "addons"
        if blender_config.exists():
            plugin_dir = blender_config
        
        if not plugin_dir:
            # Try system-wide installation
            system_addons = root_dir / f"{major}.{minor}" / "scripts" / "addons"
            if system_addons.exists():
                plugin_dir = system_addons
    else:
        # Linux and other Unix-like systems
        # Try XDG config directory first
        xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        blender_config = xdg_config / "blender" / f"{major}.{minor}" / "scripts" / "addons"
        if blender_config.exists():
            plugin_dir = blender_config

        if not plugin_dir:
            # Try system-wide installation
            system_addons = root_dir / f"{major}.{minor}" / "scripts" / "addons"
            if system_addons.exists():
                plugin_dir = system_addons

    if not plugin_dir:
        # Ask user for plugin directory
        plugin_dir_input = click.prompt(
            "Could not detect Blender addons directory. Please enter the path"
        )
        plugin_dir = Path(plugin_dir_input)

        if not plugin_dir.exists():
            raise click.ClickException(f"Addons directory not found: {plugin_dir}")

    return {
        "version": version,
        "exec_path": str(blender_path_obj),
        "root_dir": str(root_dir),
        "plugin_dir": str(plugin_dir),
    }


def get_addon_zip_path() -> Path:
    """Get path to the addon zip file"""
    # Check if we're in development mode
    current_dir = Path.cwd()

    # Look for addon in development directory
    dev_addon_dir = current_dir / "blender_addon" / "bld_remote_mcp"
    dev_addon_zip = current_dir / "blender_addon" / "bld_remote_mcp.zip"

    if dev_addon_dir.exists():
        # Create zip from development directory
        if dev_addon_zip.exists():
            dev_addon_zip.unlink()

        # Create zip
        shutil.make_archive(
            str(dev_addon_zip.with_suffix("")),
            "zip",
            str(dev_addon_dir.parent),
            "bld_remote_mcp",
        )
        return dev_addon_zip

    # Look for installed package data
    try:
        import pkg_resources

        package_data = pkg_resources.resource_filename("blender_remote", "addon")
        if Path(package_data).exists():
            return Path(package_data) / "bld_remote_mcp.zip"
    except Exception:
        pass

    raise click.ClickException("Could not find bld_remote_mcp addon files")


def get_debug_addon_zip_path() -> Path:
    """Get path to the debug addon zip file"""
    # Check if we're in development mode
    current_dir = Path.cwd()

    # Look for debug addon in development directory
    dev_addon_dir = current_dir / "blender_addon" / "simple-tcp-executor"
    dev_addon_zip = current_dir / "blender_addon" / "simple-tcp-executor.zip"

    if dev_addon_dir.exists():
        # Create zip from development directory
        if dev_addon_zip.exists():
            dev_addon_zip.unlink()

        # Create zip
        shutil.make_archive(
            str(dev_addon_zip.with_suffix("")),
            "zip",
            str(dev_addon_dir.parent),
            "simple-tcp-executor",
        )
        return dev_addon_zip

    raise click.ClickException("Could not find simple-tcp-executor addon files")


def connect_and_send_command(
    command_type: str,
    params: dict[str, Any] | None = None,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Connect to BLD_Remote_MCP and send a command with optimized socket handling"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        command = {"type": command_type, "params": params or {}}

        # Send command
        command_json = json.dumps(command)
        sock.sendall(command_json.encode("utf-8"))

        # Optimized response handling with accumulation (matches MCP server approach)
        response_data = b''

        while len(response_data) < SOCKET_MAX_RESPONSE_SIZE:
            try:
                chunk = sock.recv(SOCKET_RECV_CHUNK_SIZE)
                if not chunk:
                    break
                response_data += chunk

                # Quick check if we might have complete JSON by looking for balanced braces
                try:
                    decoded = response_data.decode("utf-8")
                    if decoded.count('{') > 0 and decoded.count('{') == decoded.count('}'):
                        # Likely complete JSON, try parsing
                        response = json.loads(decoded)
                        sock.close()
                        return cast(dict[str, Any], response)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # Not ready yet, continue reading
                    continue

            except TimeoutError:
                # Short timeout means likely no more data for LAN/localhost
                break
            except Exception as e:
                if "timeout" in str(e).lower():
                    break
                else:
                    raise e

        if not response_data:
            sock.close()
            return {"status": "error", "message": "Connection closed by Blender"}

        # Final parse attempt
        response = json.loads(response_data.decode("utf-8"))
        sock.close()
        return cast(dict[str, Any], response)

    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {e}"}


@click.group()
@click.version_option(version="1.2.0-rc2")
def cli() -> None:
    """Enhanced CLI tools for blender-remote"""
    pass


@cli.command()
@click.argument("blender_path", type=click.Path(exists=True), required=False)
@click.option("--backup", is_flag=True, help="Create backup of existing config")
def init(blender_path: str | None, backup: bool) -> None:
    """Initialize blender-remote configuration.
    
    If blender_path is not provided, you will be prompted to enter the path.
    """
    click.echo("🔧 Initializing blender-remote configuration...")

    # Backup existing config if requested
    if backup and CONFIG_FILE.exists():
        backup_path = CONFIG_FILE.with_suffix(".yaml.bak")
        shutil.copy2(CONFIG_FILE, backup_path)
        click.echo(f"📋 Backup created: {backup_path}")

    # Get blender path - prompt if not provided
    if not blender_path:
        blender_path = click.prompt(
            "Please enter the path to your Blender executable",
            type=click.Path(exists=True)
        )

    # Detect Blender info
    click.echo("🔍 Detecting Blender information...")
    blender_info = detect_blender_info(blender_path)

    # Create config
    config = {
        "blender": blender_info,
        "mcp_service": {
            "default_port": DEFAULT_PORT,
            "log_level": "INFO"
        }
    }

    # Save config
    config_manager = BlenderRemoteConfig()
    config_manager.save(config)

    # Display results
    click.echo("✅ Configuration initialized successfully!")
    click.echo(f"📁 Config file: {CONFIG_FILE}")
    click.echo(f"🎨 Blender version: {blender_info['version']}")
    click.echo(f"📂 Blender executable: {blender_info['exec_path']}")
    click.echo(f"📂 Blender root directory: {blender_info['root_dir']}")
    click.echo(f"📂 Plugin directory: {blender_info['plugin_dir']}")
    click.echo(f"🔌 Default MCP port: {DEFAULT_PORT}")
    click.echo("📊 Default log level: INFO")


@cli.command()
def install() -> None:
    """Install bld_remote_mcp addon to Blender"""
    click.echo("🔧 Installing bld_remote_mcp addon...")

    # Load config
    config = BlenderRemoteConfig()
    blender_config = config.get("blender")

    if not blender_config:
        raise click.ClickException("Blender configuration not found. Run 'init' first.")

    blender_path = blender_config.get("exec_path")

    if not blender_path:
        raise click.ClickException("Blender executable path not found in config")

    # Get addon zip path
    addon_zip = get_addon_zip_path()

    click.echo(f"📦 Using addon: {addon_zip}")

    # Install addon using Blender CLI
    # Use as_posix() to ensure forward slashes on all platforms
    addon_zip_posix = addon_zip.as_posix()
    python_expr = f"import bpy; bpy.ops.preferences.addon_install(filepath='{addon_zip_posix}', overwrite=True); bpy.ops.preferences.addon_enable(module='bld_remote_mcp'); bpy.ops.wm.save_userpref()"

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python-expr", python_expr],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            click.echo("✅ Addon installed successfully!")
            click.echo(
                f"📁 Addon location: {blender_config.get('plugin_dir')}/bld_remote_mcp"
            )
        else:
            click.echo("❌ Installation failed!")
            click.echo(f"Error: {result.stderr}")
            raise click.ClickException("Addon installation failed")

    except subprocess.TimeoutExpired:
        raise click.ClickException("Installation timeout")
    except Exception as e:
        raise click.ClickException(f"Installation error: {e}")


@cli.group()
def config() -> None:
    """Manage blender-remote configuration"""
    pass


@config.command()
@click.argument("key_value", required=False)
def set(key_value: str | None) -> None:
    """Set configuration value (format: key=value)"""
    if not key_value:
        raise click.ClickException("Usage: config set key=value")

    if "=" not in key_value:
        raise click.ClickException("Usage: config set key=value")

    key, value = key_value.split("=", 1)

    # Try to parse as int, float, or bool
    parsed_value: Any
    if value.isdigit():
        parsed_value = int(value)
    elif value.replace(".", "", 1).isdigit():
        parsed_value = float(value)
    elif value.lower() in ("true", "false"):
        parsed_value = value.lower() == "true"
    else:
        parsed_value = value

    config_manager = BlenderRemoteConfig()
    config_manager.set(key, parsed_value)

    click.echo(f"✅ Set {key} = {parsed_value}")


@config.command()
@click.argument("key", required=False)
def get(key: str | None) -> None:
    """Get configuration value(s)"""
    config_manager = BlenderRemoteConfig()

    if key:
        value = config_manager.get(key)
        if value is None:
            click.echo(f"❌ Key '{key}' not found")
        else:
            click.echo(f"{key} = {value}")
    else:
        config_manager.load()
        click.echo(OmegaConf.to_yaml(config_manager.config))


@cli.command()
@click.option("--background", is_flag=True, help="Start Blender in background mode")
@click.option(
    "--pre-file",
    type=click.Path(exists=True),
    help="Python file to execute before startup",
)
@click.option("--pre-code", help="Python code to execute before startup")
@click.option("--port", type=int, help="Override default MCP port")
@click.option(
    "--scene",
    type=click.Path(exists=True),
    help="Open specified .blend scene file",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Override logging level for BLD_Remote_MCP",
)
@click.argument("blender_args", nargs=-1, type=click.UNPROCESSED)
def start(
    background: bool,
    pre_file: str | None,
    pre_code: str | None,
    port: int | None,
    scene: str | None,
    log_level: str | None,
    blender_args: tuple,
) -> int | None:
    """Start Blender with BLD_Remote_MCP service"""

    if pre_file and pre_code:
        raise click.ClickException("Cannot use both --pre-file and --pre-code options")

    # Load config
    config = BlenderRemoteConfig()
    blender_config = config.get("blender")

    if not blender_config:
        raise click.ClickException("Blender configuration not found. Run 'init' first.")

    blender_path = blender_config.get("exec_path")
    mcp_port = port or config.get("mcp_service.default_port") or DEFAULT_PORT
    mcp_log_level = log_level or config.get("mcp_service.log_level") or "INFO"

    # Prepare startup code
    startup_code = []

    # Add pre-code if provided
    if pre_file:
        with open(pre_file) as f:
            startup_code.append(f.read())
    elif pre_code:
        startup_code.append(pre_code)

    # Add MCP service startup code
    startup_code.append(
        f"""
# Start BLD Remote MCP service
import os
os.environ['BLD_REMOTE_MCP_PORT'] = '{mcp_port}'
os.environ['BLD_REMOTE_MCP_START_NOW'] = '1'
os.environ['BLD_REMOTE_LOG_LEVEL'] = '{mcp_log_level.upper()}'

try:
    import bld_remote
    bld_remote.start_mcp_service()
    print(f"✅ BLD Remote MCP service started on port {mcp_port} (log level: {mcp_log_level.upper()})")
except Exception as e:
    print(f"❌ Failed to start BLD Remote MCP service: {{e}}")
"""
    )

    # In background mode, add proper keep-alive mechanism
    if background:
        startup_code.append(
            """
# Keep Blender running in background mode
import time
import signal
import sys
import threading

# Global flag to control the keep-alive loop
_keep_running = True

def signal_handler(signum, frame):
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
    
    print("✅ Starting main background loop...")
    
    # Import BLD Remote module for status checking
    import bld_remote
    
    # Verify service started successfully
    status = bld_remote.get_status()
    if status.get('running'):
        print(f"✅ MCP service is running on port {status.get('port')}")
    else:
        print("⚠️ Warning: MCP service may not have started properly")
    
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
        )

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write("\n".join(startup_code))
        temp_script = temp_file.name

    try:
        # Build command
        cmd = [blender_path]

        # Add scene file if provided (must come before --background for background mode)
        if scene:
            cmd.append(scene)

        if background:
            cmd.append("--background")

        cmd.extend(["--python", temp_script])

        # Add additional blender arguments
        if blender_args:
            cmd.extend(blender_args)

        click.echo(f"🚀 Starting Blender with BLD_Remote_MCP on port {mcp_port}...")

        if scene:
            click.echo(f"📁 Opening scene: {scene}")

        if log_level:
            click.echo(f"📊 Log level override: {mcp_log_level.upper()}")

        if background:
            click.echo("🔧 Background mode: Blender will run headless")
        else:
            click.echo("🖥️  GUI mode: Blender window will open")

        # Execute Blender
        result = subprocess.run(cmd, timeout=None)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass


# Code execution commands with base64 support
@cli.command()
@click.argument("code_file", type=click.Path(exists=True), required=False)
@click.option("--code", "-c", help="Python code to execute directly")
@click.option("--use-base64", is_flag=True, help="Use base64 encoding for code transmission (recommended for complex code)")
@click.option("--return-base64", is_flag=True, help="Request base64-encoded results (recommended for complex output)")
@click.option("--port", type=int, help="Override default MCP port")
def execute(code_file: str | None, code: str | None, use_base64: bool, return_base64: bool, port: int | None) -> None:
    """Execute Python code in Blender with optional base64 encoding"""

    if not code_file and not code:
        raise click.ClickException("Must provide either --code or a code file")

    if code_file and code:
        raise click.ClickException("Cannot use both --code and code file")

    # Read code from file if provided
    if code_file:
        with open(code_file) as f:
            code_to_execute = f.read()
        click.echo(f"📁 Executing code from: {code_file}")
    else:
        code_to_execute = code or ""
        click.echo("💻 Executing code directly")

    if not code_to_execute.strip():
        raise click.ClickException("Code is empty")

    if use_base64:
        click.echo("🔐 Using base64 encoding for code transmission")
    if return_base64:
        click.echo("🔐 Requesting base64-encoded results")

    click.echo(f"📏 Code length: {len(code_to_execute)} characters")

    # Get port configuration
    config = BlenderRemoteConfig()
    mcp_port = port or config.get("mcp_service.default_port") or DEFAULT_PORT

    # Prepare command parameters
    params = {
        "code": code_to_execute,
        "code_is_base64": use_base64,
        "return_as_base64": return_base64
    }

    # Encode code as base64 if requested
    if use_base64:
        encoded_code = base64.b64encode(code_to_execute.encode('utf-8')).decode('ascii')
        params["code"] = encoded_code
        click.echo(f"🔐 Encoded code length: {len(encoded_code)} characters")

    click.echo(f"📡 Connecting to Blender BLD_Remote_MCP service (port {mcp_port})...")

    # Execute command
    response = connect_and_send_command("execute_code", params, port=mcp_port)

    if response.get("status") == "success":
        result = response.get("result", {})

        click.echo("✅ Code execution successful!")

        # Handle execution result
        if result.get("executed", False):
            output = result.get("result", "")

            # Decode base64 result if needed
            if return_base64 and result.get("result_is_base64", False):
                try:
                    decoded_output = base64.b64decode(output.encode('ascii')).decode('utf-8')
                    click.echo("🔐 Decoded base64 result:")
                    click.echo(decoded_output)
                except Exception as e:
                    click.echo(f"❌ Failed to decode base64 result: {e}")
                    click.echo(f"Raw result: {output}")
            else:
                if output:
                    click.echo("📄 Output:")
                    click.echo(output)
                else:
                    click.echo("✅ Code executed successfully (no output)")
        else:
            click.echo("⚠️ Code execution completed but execution status unclear")
            click.echo(f"Response: {result}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"❌ Code execution failed: {error_msg}")
        if "connection" in error_msg.lower():
            click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")


# Legacy commands for backward compatibility
@cli.command()
def status() -> None:
    """Check connection status to Blender"""
    click.echo("🔍 Checking connection to Blender BLD_Remote_MCP service...")

    config = BlenderRemoteConfig()
    port = config.get("mcp_service.default_port") or DEFAULT_PORT

    response = connect_and_send_command("get_scene_info", port=port)

    if response.get("status") == "success":
        click.echo(f"✅ Connected to Blender BLD_Remote_MCP service (port {port})")
        scene_info = response.get("result", {})
        scene_name = scene_info.get("name", "Unknown")
        object_count = scene_info.get("object_count", 0)
        click.echo(f"   Scene: {scene_name}")
        click.echo(f"   Objects: {object_count}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"❌ Connection failed: {error_msg}")
        click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")


# Debug commands for testing code execution patterns
@cli.group()
def debug() -> None:
    """Debug tools for testing code execution patterns"""
    pass


@debug.command()
def install() -> None:
    """Install simple-tcp-executor debug addon to Blender"""
    click.echo("🔧 Installing simple-tcp-executor debug addon...")

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

    click.echo(f"📦 Using debug addon: {debug_addon_zip}")

    # Install addon using Blender CLI
    # Use as_posix() to ensure forward slashes on all platforms
    debug_addon_zip_posix = debug_addon_zip.as_posix()
    python_expr = f"import bpy; bpy.ops.preferences.addon_install(filepath='{debug_addon_zip_posix}', overwrite=True); bpy.ops.preferences.addon_enable(module='simple-tcp-executor'); bpy.ops.wm.save_userpref()"

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python-expr", python_expr],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            click.echo("✅ Debug addon installed successfully!")
            click.echo(
                f"📁 Addon location: {blender_config.get('plugin_dir')}/simple-tcp-executor"
            )
        else:
            click.echo("❌ Installation failed!")
            click.echo(f"Error: {result.stderr}")
            raise click.ClickException("Debug addon installation failed")

    except subprocess.TimeoutExpired:
        raise click.ClickException("Installation timeout")
    except Exception as e:
        raise click.ClickException(f"Installation error: {e}")


@debug.command()
@click.option("--background", is_flag=True, help="Start Blender in background mode")
@click.option("--port", type=int, help="TCP port for debug server (default: 7777 or BLD_DEBUG_TCP_PORT env var)")
def start(background: bool, port: int | None) -> None:
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
    print(f"✅ Simple TCP Executor debug addon enabled on port {debug_port}")
except Exception as e:
    print(f"❌ Failed to enable debug addon: {{e}}")
    print("Make sure the addon is installed first using 'debug install'")
"""

    if background:
        startup_code += """
# Keep Blender running in background mode
import time
import signal
import sys

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
    print("✅ Starting debug background loop...")
    
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

        click.echo(f"🚀 Starting Blender with debug TCP server on port {debug_port}...")

        if background:
            click.echo("🔧 Background mode: Blender will run headless")
        else:
            click.echo("🖥️  GUI mode: Blender window will open")

        # Execute Blender
        result = subprocess.run(cmd, timeout=None)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass


if __name__ == "__main__":
    cli()
