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

# Windows-specific imports
try:
    import winreg
except ImportError:
    winreg = None  # Not available on non-Windows systems

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


def find_blender_executable_macos() -> str | None:
    """Find Blender executable on macOS using multiple methods"""
    click.echo("  → Checking common installation locations...")
    
    # Common locations for Blender on macOS
    possible_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
        Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
    ]
    
    # Check each path
    for path in possible_paths:
        if Path(path).exists():
            return str(path)
    
    # Use mdfind (Spotlight) to search for Blender.app
    click.echo("  → Searching with Spotlight (mdfind)...")
    try:
        result = subprocess.run(
            ["mdfind", "-name", "Blender.app"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            # Get first result
            app_path = result.stdout.strip().split('\n')[0]
            blender_exe = Path(app_path) / "Contents/MacOS/Blender"
            if blender_exe.exists():
                return str(blender_exe)
    except Exception:
        pass
    
    return None


def find_blender_executable_windows() -> str | None:
    """Find Blender executable on Windows using registry and common paths"""
    if winreg is None:
        click.echo("  → Windows registry module not available")
        return None
    
    click.echo("  → Searching Windows Registry for Blender 4.x installations...")
    
    # First try registry search (most reliable for MSI installations)
    blender_paths = []
    uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    
    for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for arch_key in [0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                with winreg.OpenKey(hkey, uninstall_key_path, 0, winreg.KEY_READ | arch_key) as uninstall_key:
                    for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                if "blender" in display_name.lower() and display_version.startswith("4."):
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    if install_location:
                                        blender_exe = Path(install_location) / "blender.exe"
                                        if blender_exe.exists():
                                            click.echo(f"  → Found {display_name} {display_version} at: {install_location}")
                                            return str(blender_exe)
                                        blender_paths.append(install_location)
                            except OSError:
                                continue
            except OSError:
                continue
    
    # If registry search found paths but no valid executable, show them
    if blender_paths:
        click.echo("  → Found installation paths in registry but no valid blender.exe:")
        for path in set(blender_paths):
            click.echo(f"    - {path}")
    
    # Try common installation paths as fallback
    click.echo("  → Checking common installation locations...")
    common_paths = [
        "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe",
        "C:\\Program Files\\Blender Foundation\\Blender 4.3\\blender.exe",
        "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
        "C:\\Program Files\\Blender Foundation\\Blender 4.1\\blender.exe",
        "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
        "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Blender\\blender.exe",
    ]
    
    for path in common_paths:
        if Path(path).exists():
            click.echo(f"  → Found Blender at: {path}")
            return str(path)
    
    # Try to find via Windows PATH
    click.echo("  → Checking if blender.exe is in system PATH...")
    try:
        result = subprocess.run(
            ["where", "blender"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            blender_exe = result.stdout.strip().split('\n')[0]
            if Path(blender_exe).exists():
                click.echo(f"  → Found Blender in PATH: {blender_exe}")
                return str(blender_exe)
    except Exception:
        pass
    
    return None


def detect_blender_info(blender_path: str | Path) -> dict[str, Any]:
    """Detect Blender version and paths using Blender's Python APIs"""
    blender_path_obj = Path(blender_path)

    if not blender_path_obj.exists():
        raise click.ClickException(f"Blender executable not found: {blender_path_obj}")

    click.echo(f"Detecting Blender info: {blender_path_obj}")
    click.echo("  → Creating detection script...")

    # Create temporary detection script
    detection_script = '''
import bpy
import sys
import json
import os

try:
    # Get version information
    version_info = {
        "version_string": bpy.app.version_string,
        "version_tuple": bpy.app.version,
        "build_date": bpy.app.build_date.decode('utf-8'),
    }
    
    # Get addon directory paths
    try:
        user_scripts = bpy.utils.user_resource('SCRIPTS')
        user_addons = os.path.join(user_scripts, 'addons') if user_scripts else None
    except:
        user_addons = None
    
    try:
        all_addon_paths = bpy.utils.script_paths(subdir="addons")
    except:
        all_addon_paths = []
    
    addon_paths = {
        "user_addons": user_addons,
        "all_addon_paths": all_addon_paths,
    }
    
    # Try to get extensions directory (Blender 4.2+)
    try:
        addon_paths["extensions"] = bpy.utils.user_resource('EXTENSIONS')
    except:
        addon_paths["extensions"] = None
    
    # Combine all information
    result = {
        "version": version_info,
        "paths": addon_paths,
        "success": True
    }
    
    print(json.dumps(result, indent=2))
    
except Exception as e:
    error_result = {
        "success": False,
        "error": str(e),
        "error_type": type(e).__name__
    }
    print(json.dumps(error_result, indent=2))
    
sys.exit(0)
'''

    # Create and execute temporary script
    temp_script = None
    try:
        # Create temporary file
        temp_fd, temp_script = tempfile.mkstemp(suffix='.py', text=True)
        with os.fdopen(temp_fd, 'w') as f:
            f.write(detection_script)

        # Execute Blender with the detection script
        click.echo("  → Starting Blender in background mode (this may take a moment)...")
        result = subprocess.run(
            [str(blender_path_obj), "--background", "--python", temp_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        click.echo("  → Blender execution completed, processing results...")

        if result.returncode != 0:
            raise click.ClickException(f"Blender detection script failed: {result.stderr}")

        # Parse JSON output (extract JSON from mixed output)
        try:
            # Look for JSON in the output (it should be the last valid JSON block)
            lines = result.stdout.strip().split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                if line.strip().startswith('{') and not in_json:
                    in_json = True
                    json_lines = [line]
                elif in_json:
                    json_lines.append(line)
                    if line.strip() == '}':
                        # Try to parse this JSON block
                        try:
                            json_text = '\n'.join(json_lines)
                            detection_data = json.loads(json_text)
                            break
                        except json.JSONDecodeError:
                            # Continue looking for valid JSON
                            continue
            else:
                # No valid JSON found
                raise click.ClickException(f"No valid JSON found in Blender output. Raw output: {result.stdout}")
            
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Failed to parse Blender detection output: {e}\nOutput: {result.stdout}")

        if not detection_data.get("success"):
            error_msg = detection_data.get("error", "Unknown error")
            raise click.ClickException(f"Blender detection failed: {error_msg}")

        # Extract version information
        version_info = detection_data["version"]
        version_string = version_info["version_string"]
        version_tuple = version_info["version_tuple"]
        build_date = version_info["build_date"]

        click.echo(f"Found Blender {version_string}")

        # Check version compatibility
        major, minor, _ = version_tuple
        if major < 4:
            raise click.ClickException(
                f"Blender version {version_string} is not supported. Please use Blender 4.0 or higher."
            )

        # Extract path information
        paths_info = detection_data["paths"]
        user_addons = paths_info.get("user_addons")
        all_addon_paths = paths_info.get("all_addon_paths", [])
        extensions_dir = paths_info.get("extensions")

        # Determine primary addon directory
        plugin_dir = None
        if user_addons and os.path.exists(user_addons):
            plugin_dir = user_addons
            click.echo(f"Using user addon directory: {plugin_dir}")
        elif all_addon_paths:
            # Find the first writable addon path
            for path in all_addon_paths:
                if os.path.exists(path):
                    try:
                        # Test if directory is writable
                        test_file = os.path.join(path, '.test_write')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        plugin_dir = path
                        click.echo(f"Using writable addon directory: {plugin_dir}")
                        break
                    except (OSError, IOError):
                        continue

        # Create addon directory if it doesn't exist
        if not plugin_dir and user_addons:
            try:
                os.makedirs(user_addons, exist_ok=True)
                plugin_dir = user_addons
                click.echo(f"Created addon directory: {plugin_dir}")
            except OSError as e:
                click.echo(f"Warning: Could not create addon directory: {e}")

        # Fallback to manual detection if no directory found
        if not plugin_dir:
            # Show detected paths for debugging
            click.echo(f"Searched paths:")
            if user_addons:
                click.echo(f"  - {user_addons}")
            for path in all_addon_paths:
                if path != user_addons:
                    click.echo(f"  - {path}")
            
            # Ask user for plugin directory
            click.echo("Could not automatically detect writable addon directory.")
            
            plugin_dir_input = click.prompt(
                "Please enter the path to your Blender addons directory"
            )
            plugin_dir = Path(plugin_dir_input)

            if not plugin_dir.exists():
                raise click.ClickException(f"Addons directory not found: {plugin_dir}")

        # Detect root directory
        root_dir = blender_path_obj.parent

        # Show searched paths summary
        click.echo(f"Searched paths:")
        if user_addons:
            click.echo(f"  - {user_addons}")
        for path in all_addon_paths:
            if path != user_addons:
                click.echo(f"  - {path}")
        click.echo(f"Selected addon directory: {plugin_dir}")

        return {
            "version": version_string,
            "version_tuple": version_tuple,
            "build_date": build_date,
            "exec_path": str(blender_path_obj),
            "root_dir": str(root_dir),
            "plugin_dir": str(plugin_dir),
            "user_addons": user_addons,
            "all_addon_paths": all_addon_paths,
            "extensions_dir": extensions_dir,
        }

    except subprocess.TimeoutExpired:
        raise click.ClickException("Timeout while detecting Blender info")
    except Exception as e:
        raise click.ClickException(f"Error detecting Blender info: {e}")
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass  # Ignore cleanup errors


def get_addon_zip_path() -> Path:
    """Get path to the addon zip file"""
    # Check if we're in development mode
    current_dir = Path.cwd()

    # Look for addon in development directory (legacy location)
    dev_addon_dir = current_dir / "blender_addon" / "bld_remote_mcp"

    if dev_addon_dir.exists():
        # Create zip in system temp directory to avoid cluttering workspace
        temp_dir = Path(tempfile.gettempdir())
        dev_addon_zip = temp_dir / "bld_remote_mcp.zip"
        
        # Remove existing temp zip if present
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
        # Try modern importlib approach first
        try:
            import importlib.resources as importlib_resources
            package_path = importlib_resources.files("blender_remote") / "addon" / "bld_remote_mcp"
            if package_path.exists():
                addon_dir = package_path
        except (ImportError, AttributeError):
            # Fallback to older importlib.resources API
            try:
                import importlib_resources
                package_path = importlib_resources.files("blender_remote") / "addon" / "bld_remote_mcp"
                if package_path.exists():
                    addon_dir = package_path
            except ImportError:
                # Final fallback to pkg_resources
                import pkg_resources
                addon_dir = Path(pkg_resources.resource_filename("blender_remote", "addon/bld_remote_mcp"))
        
        if addon_dir and Path(addon_dir).exists():
            # Create zip from installed package data
            temp_dir = Path(tempfile.gettempdir())
            addon_zip = temp_dir / "bld_remote_mcp.zip"
            
            # Remove existing temp zip if present
            if addon_zip.exists():
                addon_zip.unlink()
            
            # Create zip from package data
            shutil.make_archive(
                str(addon_zip.with_suffix("")),
                "zip",
                str(Path(addon_dir).parent),
                "bld_remote_mcp",
            )
            return addon_zip
    except Exception:
        pass

    raise click.ClickException("Could not find bld_remote_mcp addon files")


def get_debug_addon_zip_path() -> Path:
    """Get path to the debug addon zip file"""
    # Check if we're in development mode
    current_dir = Path.cwd()

    # Look for debug addon in development directory (legacy location)
    dev_addon_dir = current_dir / "blender_addon" / "simple-tcp-executor"

    if dev_addon_dir.exists():
        # Create zip in system temp directory to avoid cluttering workspace
        temp_dir = Path(tempfile.gettempdir())
        dev_addon_zip = temp_dir / "simple-tcp-executor.zip"
        
        # Remove existing temp zip if present
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

    # Look for installed package data
    try:
        # Try modern importlib approach first
        try:
            import importlib.resources as importlib_resources
            package_path = importlib_resources.files("blender_remote") / "addon" / "simple-tcp-executor"
            if package_path.exists():
                addon_dir = package_path
        except (ImportError, AttributeError):
            # Fallback to older importlib.resources API
            try:
                import importlib_resources
                package_path = importlib_resources.files("blender_remote") / "addon" / "simple-tcp-executor"
                if package_path.exists():
                    addon_dir = package_path
            except ImportError:
                # Final fallback to pkg_resources
                import pkg_resources
                addon_dir = Path(pkg_resources.resource_filename("blender_remote", "addon/simple-tcp-executor"))
        
        if addon_dir and Path(addon_dir).exists():
            # Create zip from installed package data
            temp_dir = Path(tempfile.gettempdir())
            addon_zip = temp_dir / "simple-tcp-executor.zip"
            
            # Remove existing temp zip if present
            if addon_zip.exists():
                addon_zip.unlink()
            
            # Create zip from package data
            shutil.make_archive(
                str(addon_zip.with_suffix("")),
                "zip",
                str(Path(addon_dir).parent),
                "simple-tcp-executor",
            )
            return addon_zip
    except Exception:
        pass

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
@click.version_option(version="1.2.1")
def cli() -> None:
    """Enhanced CLI tools for blender-remote"""
    pass


@cli.command()
@click.argument("blender_path", type=click.Path(exists=True), required=False)
@click.option("--backup", is_flag=True, help="Create backup of existing config")
def init(blender_path: str | None, backup: bool) -> None:
    """Initialize blender-remote configuration.

    On macOS and Windows, if blender_path is not provided, will attempt auto-detection.
    On other platforms, you will be prompted to enter the path.
    """
    click.echo("Initializing blender-remote configuration...")

    # Backup existing config if requested
    if backup and CONFIG_FILE.exists():
        backup_path = CONFIG_FILE.with_suffix(".yaml.bak")
        shutil.copy2(CONFIG_FILE, backup_path)
        click.echo(f"Backup created: {backup_path}")

    # Get blender path - auto-detect on macOS and Windows if not provided
    if not blender_path:
        current_platform = platform.system()
        
        if current_platform == "Darwin":  # macOS
            click.echo("Attempting to auto-detect Blender on macOS...")
            detected_path = find_blender_executable_macos()
            
            if detected_path:
                click.echo(f"Found Blender at: {detected_path}")
                use_detected = click.confirm(
                    "Use this detected path?",
                    default=True
                )
                
                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True)
                    )
            else:
                click.echo("Could not auto-detect Blender on macOS")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True)
                )
        elif current_platform == "Windows":  # Windows
            click.echo("Attempting to auto-detect Blender on Windows...")
            detected_path = find_blender_executable_windows()
            
            if detected_path:
                click.echo(f"Found Blender at: {detected_path}")
                use_detected = click.confirm(
                    "Use this detected path?",
                    default=True
                )
                
                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True)
                    )
            else:
                click.echo("Could not auto-detect Blender on Windows")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True)
                )
        else:
            # For other platforms, prompt for path
            blender_path = click.prompt(
                "Please enter the path to your Blender executable",
                type=click.Path(exists=True)
            )

    # Detect Blender info
    click.echo("\nAnalyzing Blender installation...")
    blender_info = detect_blender_info(blender_path)

    # Create config
    click.echo("  → Generating configuration structure...")
    config = {
        "blender": blender_info,
        "mcp_service": {
            "default_port": DEFAULT_PORT,
            "log_level": "INFO"
        }
    }

    # Save config
    click.echo("  → Saving configuration...")
    config_manager = BlenderRemoteConfig()
    config_manager.save(config)

    # Display final configuration
    click.echo(f"\n✅ Configuration saved to: {CONFIG_FILE}")
    click.echo("\n📋 Generated configuration:")
    
    # Display the configuration like 'config get' does
    config_yaml = OmegaConf.to_yaml(config)
    click.echo(config_yaml)
    
    click.echo("✅ Initialization complete! You can now use other blender-remote-cli commands.")


@cli.command()
def install() -> None:
    """Install bld_remote_mcp addon to Blender.
    
    If no configuration exists, will attempt to auto-detect Blender on Windows and macOS.
    """
    click.echo("[INSTALL] Installing bld_remote_mcp addon...")

    # Try to load existing config
    config = BlenderRemoteConfig()
    blender_config = None
    blender_path = None
    
    try:
        blender_config = config.get("blender")
        if blender_config:
            blender_path = blender_config.get("exec_path")
    except click.ClickException:
        # Config file doesn't exist
        pass

    # If no config or no blender path, try auto-detection
    if not blender_config or not blender_path:
        current_platform = platform.system()
        
        if current_platform == "Windows":
            click.echo("[AUTO-DETECT] Attempting to auto-detect Blender on Windows...")
            detected_path = find_blender_executable_windows()
            
            if detected_path:
                click.echo(f"[FOUND] Blender found at: {detected_path}")
                use_detected = click.confirm(
                    "Use this detected path?",
                    default=True
                )
                
                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True)
                    )
            else:
                click.echo("[NOT FOUND] Could not auto-detect Blender on Windows")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True)
                )
        elif current_platform == "Darwin":  # macOS
            click.echo("[AUTO-DETECT] Attempting to auto-detect Blender on macOS...")
            detected_path = find_blender_executable_macos()
            
            if detected_path:
                click.echo(f"[FOUND] Blender found at: {detected_path}")
                use_detected = click.confirm(
                    "Use this detected path?",
                    default=True
                )
                
                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True)
                    )
            else:
                click.echo("[NOT FOUND] Could not auto-detect Blender on macOS")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True)
                )
        else:
            # For other platforms, prompt for path
            click.echo("[MANUAL] Please enter your Blender executable path:")
            blender_path = click.prompt(
                "Path to Blender executable",
                type=click.Path(exists=True)
            )
        
        # If we got a blender path, detect its info and save config
        if blender_path:
            click.echo(f"[CONFIG] Analyzing Blender installation at: {blender_path}")
            try:
                blender_info = detect_blender_info(blender_path)
                
                # Create and save config
                new_config = {
                    "blender": blender_info,
                    "mcp_service": {
                        "default_port": DEFAULT_PORT,
                        "log_level": "INFO"
                    }
                }
                
                config.save(new_config)
                click.echo(f"[CONFIG] Configuration saved to: {CONFIG_FILE}")
                blender_config = blender_info
                
            except Exception as e:
                raise click.ClickException(f"Failed to analyze Blender installation: {e}")
        else:
            raise click.ClickException("No Blender executable path provided")
    
    # At this point we should have a valid blender_path and blender_config
    if not blender_path:
        raise click.ClickException("Blender executable path not found")

    # Get addon zip path
    addon_zip = get_addon_zip_path()

    click.echo(f"[ADDON] Using addon: {addon_zip}")

    # Create Python script for addon installation
    # Use as_posix() to ensure forward slashes on all platforms
    addon_zip_posix = addon_zip.as_posix()
    
    install_script = f'''
import bpy
import sys
import os

def install_and_enable_addon(addon_zip_path, addon_module_name):
    """
    Installs and enables a Blender addon.
    
    :param addon_zip_path: Absolute path to the addon's .zip file.
    :param addon_module_name: The module name of the addon to enable.
    """
    if not os.path.exists(addon_zip_path):
        print(f"Error: Addon file not found at '{{addon_zip_path}}'")
        sys.exit(1)

    try:
        print(f"Installing addon from: {{addon_zip_path}}")
        bpy.ops.preferences.addon_install(filepath=addon_zip_path, overwrite=True)
        
        print(f"Enabling addon: {{addon_module_name}}")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
        
        print("Saving user preferences...")
        bpy.ops.wm.save_userpref()
        
        print(f"Addon '{{addon_module_name}}' installed and enabled successfully.")
        
    except Exception as e:
        print(f"An error occurred: {{e}}")
        # Attempt to get more details from the exception if possible
        if hasattr(e, 'args') and e.args:
            print("Details:", e.args[0])
        sys.exit(1)

# Main execution
addon_path = "{addon_zip_posix}"
addon_name = "bld_remote_mcp"

install_and_enable_addon(addon_path, addon_name)
'''

    # Create temporary script file
    temp_script = None
    try:
        # Create temporary file
        temp_fd, temp_script = tempfile.mkstemp(suffix='.py', text=True)
        with os.fdopen(temp_fd, 'w') as f:
            f.write(install_script)

        # Install addon using Blender CLI with Python script
        result = subprocess.run(
            [blender_path, "--background", "--python", temp_script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            click.echo("[SUCCESS] Addon installed successfully!")
            click.echo(
                f"[LOCATION] Addon location: {blender_config.get('plugin_dir')}/bld_remote_mcp"
            )
        else:
            click.echo("[ERROR] Installation failed!")
            click.echo(f"Error: {result.stderr}")
            click.echo(f"Output: {result.stdout}")
            raise click.ClickException("Addon installation failed")

    except subprocess.TimeoutExpired:
        raise click.ClickException("Installation timeout")
    except Exception as e:
        raise click.ClickException(f"Installation error: {e}")
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass  # Ignore cleanup errors


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

    click.echo(f"[SUCCESS] Set {key} = {parsed_value}")


@config.command()
@click.argument("key", required=False)
def get(key: str | None) -> None:
    """Get configuration value(s)"""
    config_manager = BlenderRemoteConfig()

    if key:
        value = config_manager.get(key)
        if value is None:
            click.echo(f"[ERROR] Key '{key}' not found")
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

    # Add MCP service startup code - environment variables are set in shell
    startup_code.append(
        """
# Verify MCP environment configuration
import os
port = os.environ.get('BLD_REMOTE_MCP_PORT', 'not set')
start_now = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'not set')
log_level = os.environ.get('BLD_REMOTE_LOG_LEVEL', 'not set')

print("[INFO] Environment: PORT=" + str(port) + ", START_NOW=" + str(start_now) + ", LOG_LEVEL=" + str(log_level))
print("[INFO] MCP service will start via addon auto-start mechanism")
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
import platform

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

        click.echo(f"[START] Starting Blender with BLD_Remote_MCP on port {mcp_port}...")

        if scene:
            click.echo(f"[SCENE] Opening scene: {scene}")

        if log_level:
            click.echo(f"[LOG] Log level override: {mcp_log_level.upper()}")

        if background:
            click.echo("[MODE] Background mode: Blender will run headless")
        else:
            click.echo("[MODE] GUI mode: Blender window will open")

        # Set up environment variables for Blender
        blender_env = os.environ.copy()
        blender_env['BLD_REMOTE_MCP_PORT'] = str(mcp_port)
        blender_env['BLD_REMOTE_MCP_START_NOW'] = '1'  # CLI always auto-starts
        blender_env['BLD_REMOTE_LOG_LEVEL'] = mcp_log_level.upper()

        # Execute Blender
        result = subprocess.run(cmd, timeout=None, env=blender_env)

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
        click.echo(f"[FILE] Executing code from: {code_file}")
    else:
        code_to_execute = code or ""
        click.echo("[CODE] Executing code directly")

    if not code_to_execute.strip():
        raise click.ClickException("Code is empty")

    if use_base64:
        click.echo("[BASE64] Using base64 encoding for code transmission")
    if return_base64:
        click.echo("[BASE64] Requesting base64-encoded results")

    click.echo(f"[LENGTH] Code length: {len(code_to_execute)} characters")

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
        click.echo(f"[ENCODED] Encoded code length: {len(encoded_code)} characters")

    click.echo(f"[CONNECT] Connecting to Blender BLD_Remote_MCP service (port {mcp_port})...")

    # Execute command
    response = connect_and_send_command("execute_code", params, port=mcp_port)

    if response.get("status") == "success":
        result = response.get("result", {})

        click.echo("[SUCCESS] Code execution successful!")

        # Handle execution result
        if result.get("executed", False):
            output = result.get("result", "")

            # Decode base64 result if needed
            if return_base64 and result.get("result_is_base64", False):
                try:
                    decoded_output = base64.b64decode(output.encode('ascii')).decode('utf-8')
                    click.echo("[DECODED] Decoded base64 result:")
                    click.echo(decoded_output)
                except Exception as e:
                    click.echo(f"[ERROR] Failed to decode base64 result: {e}")
                    click.echo(f"Raw result: {output}")
            else:
                if output:
                    click.echo("[OUTPUT] Output:")
                    click.echo(output)
                else:
                    click.echo("[SUCCESS] Code executed successfully (no output)")
        else:
            click.echo("[WARN] Code execution completed but execution status unclear")
            click.echo(f"Response: {result}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"[ERROR] Code execution failed: {error_msg}")
        if "connection" in error_msg.lower():
            click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")


# Legacy commands for backward compatibility
@cli.command()
def status() -> None:
    """Check connection status to Blender"""
    click.echo("Checking connection to Blender BLD_Remote_MCP service...")

    config = BlenderRemoteConfig()
    port = config.get("mcp_service.default_port") or DEFAULT_PORT

    response = connect_and_send_command("get_scene_info", port=port)

    if response.get("status") == "success":
        click.echo(f"Connected to Blender BLD_Remote_MCP service (port {port})")
        scene_info = response.get("result", {})
        scene_name = scene_info.get("name", "Unknown")
        object_count = scene_info.get("object_count", 0)
        click.echo(f"   Scene: {scene_name}")
        click.echo(f"   Objects: {object_count}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"Connection failed: {error_msg}")
        click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")


# Debug commands for testing code execution patterns
@cli.group()
def debug() -> None:
    """Debug tools for testing code execution patterns"""
    pass


@debug.command()
def install() -> None:
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
    
    install_script = f'''
import bpy
import sys
import os

def install_and_enable_addon(addon_zip_path, addon_module_name):
    """
    Installs and enables a Blender addon.
    
    :param addon_zip_path: Absolute path to the addon's .zip file.
    :param addon_module_name: The module name of the addon to enable.
    """
    if not os.path.exists(addon_zip_path):
        print(f"Error: Addon file not found at '{{addon_zip_path}}'")
        sys.exit(1)

    try:
        print(f"Installing addon from: {{addon_zip_path}}")
        bpy.ops.preferences.addon_install(filepath=addon_zip_path, overwrite=True)
        
        print(f"Enabling addon: {{addon_module_name}}")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
        
        print("Saving user preferences...")
        bpy.ops.wm.save_userpref()
        
        print(f"Addon '{{addon_module_name}}' installed and enabled successfully.")
        
    except Exception as e:
        print(f"An error occurred: {{e}}")
        # Attempt to get more details from the exception if possible
        if hasattr(e, 'args') and e.args:
            print("Details:", e.args[0])
        sys.exit(1)

# Main execution
addon_path = "{debug_addon_zip_posix}"
addon_name = "simple-tcp-executor"

install_and_enable_addon(addon_path, addon_name)
'''

    # Create temporary script file
    temp_script = None
    try:
        # Create temporary file
        temp_fd, temp_script = tempfile.mkstemp(suffix='.py', text=True)
        with os.fdopen(temp_fd, 'w') as f:
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

    except subprocess.TimeoutExpired:
        raise click.ClickException("Installation timeout")
    except Exception as e:
        raise click.ClickException(f"Installation error: {e}")
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass  # Ignore cleanup errors


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
        blender_env['BLD_REMOTE_MCP_START_NOW'] = 'false'  # Debug mode doesn't auto-start MCP
        blender_env['BLD_REMOTE_LOG_LEVEL'] = 'DEBUG'

        # Execute Blender
        result = subprocess.run(cmd, timeout=None, env=blender_env)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass


if __name__ == "__main__":
    cli()
