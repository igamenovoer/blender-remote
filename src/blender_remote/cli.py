"""Enhanced command-line interface for blender-remote using click.

This CLI provides comprehensive blender-remote management functionality.
The main entry point (uvx blender-remote) starts the MCP server.
"""

import os
import json
import socket
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any, cast, Union

import click
import yaml  # type: ignore[import-untyped]

CONFIG_DIR = Path.home() / ".config" / "blender-remote"
CONFIG_FILE = CONFIG_DIR / "bld-remote-config.yaml"
DEFAULT_PORT = 6688


class BlenderRemoteConfig:
    """Configuration manager for blender-remote"""

    def __init__(self) -> None:
        self.config_path = CONFIG_FILE
        self.config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            raise click.ClickException(
                f"Configuration file not found: {self.config_path}\nRun 'blender-remote-cli init <blender_path>' first"
            )

        with open(self.config_path, "r") as f:
            loaded_config = yaml.safe_load(f)
            if loaded_config is not None:
                self.config = loaded_config
        return self.config

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        self.config = config

    def get(self, key: str) -> Any:
        """Get configuration value using dot notation"""
        if not self.config:
            self.load()

        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if not self.config:
            self.load()

        keys = key.split(".")
        current = self.config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.save(self.config)


def detect_blender_info(blender_path: Union[str, Path]) -> Dict[str, Any]:
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

    # Common plugin directory patterns
    config_home = Path.home() / ".config"
    if config_home.exists():
        blender_config = (
            config_home / "blender" / f"{major}.{minor}" / "scripts" / "addons"
        )
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


def connect_and_send_command(
    command_type: str,
    params: Optional[Dict[str, Any]] = None,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Connect to BLD_Remote_MCP and send a command"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        command = {"type": command_type, "params": params or {}}

        # Send command
        command_json = json.dumps(command)
        sock.sendall(command_json.encode("utf-8"))

        # Receive response
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode("utf-8"))

        sock.close()
        return cast(Dict[str, Any], response)

    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {e}"}


@click.group()
@click.version_option(version="1.2.0-rc2")
def cli() -> None:
    """Enhanced CLI tools for blender-remote"""
    pass


@cli.command()
@click.argument("blender_path", type=click.Path(exists=True))
@click.option("--backup", is_flag=True, help="Create backup of existing config")
def init(blender_path: str, backup: bool) -> None:
    """Initialize blender-remote configuration"""
    click.echo(f"🔧 Initializing blender-remote configuration...")

    # Backup existing config if requested
    if backup and CONFIG_FILE.exists():
        backup_path = CONFIG_FILE.with_suffix(".yaml.bak")
        shutil.copy2(CONFIG_FILE, backup_path)
        click.echo(f"📋 Backup created: {backup_path}")

    # Detect Blender info
    click.echo(f"🔍 Detecting Blender information...")
    blender_info = detect_blender_info(blender_path)

    # Create config
    config = {"blender": blender_info, "mcp_service": {"default_port": DEFAULT_PORT}}

    # Save config
    config_manager = BlenderRemoteConfig()
    config_manager.save(config)

    # Display results
    click.echo(f"✅ Configuration initialized successfully!")
    click.echo(f"📁 Config file: {CONFIG_FILE}")
    click.echo(f"🎨 Blender version: {blender_info['version']}")
    click.echo(f"📂 Blender executable: {blender_info['exec_path']}")
    click.echo(f"📂 Blender root directory: {blender_info['root_dir']}")
    click.echo(f"📂 Plugin directory: {blender_info['plugin_dir']}")
    click.echo(f"🔌 Default MCP port: {DEFAULT_PORT}")


@cli.command()
def install() -> None:
    """Install bld_remote_mcp addon to Blender"""
    click.echo(f"🔧 Installing bld_remote_mcp addon...")

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
    python_expr = f"import bpy; bpy.ops.preferences.addon_install(filepath='{addon_zip}', overwrite=True); bpy.ops.preferences.addon_enable(module='bld_remote_mcp'); bpy.ops.wm.save_userpref()"

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python-expr", python_expr],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            click.echo(f"✅ Addon installed successfully!")
            click.echo(
                f"📁 Addon location: {blender_config.get('plugin_dir')}/bld_remote_mcp"
            )
        else:
            click.echo(f"❌ Installation failed!")
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
def set(key_value: Optional[str]) -> None:
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
def get(key: Optional[str]) -> None:
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
        click.echo(yaml.dump(config_manager.config, default_flow_style=False))


@cli.command()
@click.option("--background", is_flag=True, help="Start Blender in background mode")
@click.option(
    "--pre-file",
    type=click.Path(exists=True),
    help="Python file to execute before startup",
)
@click.option("--pre-code", help="Python code to execute before startup")
@click.option("--port", type=int, help="Override default MCP port")
@click.argument("blender_args", nargs=-1, type=click.UNPROCESSED)
def start(
    background: bool,
    pre_file: Optional[str],
    pre_code: Optional[str],
    port: Optional[int],
    blender_args: tuple,
) -> Optional[int]:
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

    # Prepare startup code
    startup_code = []

    # Add pre-code if provided
    if pre_file:
        with open(pre_file, "r") as f:
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

try:
    import bld_remote
    bld_remote.start_mcp_service()
    print(f"✅ BLD Remote MCP service started on port {mcp_port}")
except Exception as e:
    print(f"❌ Failed to start BLD Remote MCP service: {{e}}")
"""
    )

    # In background mode, add event loop to prevent immediate exit
    if background:
        startup_code.append(
            """
# Keep Blender running in background mode
import asyncio
import threading

def run_forever():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except KeyboardInterrupt:
        pass

# Start background thread
thread = threading.Thread(target=run_forever, daemon=True)
thread.start()

print("Blender running in background mode. Press Ctrl+C to exit.")
"""
        )

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write("\n".join(startup_code))
        temp_script = temp_file.name

    try:
        # Build command
        cmd = [blender_path]

        if background:
            cmd.append("--background")

        cmd.extend(["--python", temp_script])

        # Add additional blender arguments
        if blender_args:
            cmd.extend(blender_args)

        click.echo(f"🚀 Starting Blender with BLD_Remote_MCP on port {mcp_port}...")

        if background:
            click.echo(f"🔧 Background mode: Blender will run headless")
        else:
            click.echo(f"🖥️  GUI mode: Blender window will open")

        # Execute Blender
        result = subprocess.run(cmd, timeout=None)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass


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


if __name__ == "__main__":
    cli()
