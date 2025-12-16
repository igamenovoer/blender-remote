"""Blender installation discovery and inspection helpers for the CLI."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import click

from .constants import DETECT_BLENDER_INFO_TIMEOUT_SECONDS

# Windows-specific imports
try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]  # Not available on non-Windows systems


def find_blender_executable_macos() -> str | None:
    """Find Blender executable on macOS using multiple methods."""
    click.echo("  Ўъ Checking common installation locations...")

    # Common locations for Blender on macOS
    possible_paths: list[Path] = [
        Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        Path("/Applications/Blender/Blender.app/Contents/MacOS/Blender"),
        Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
    ]

    # Check each path
    for path in possible_paths:
        if path.exists():
            return str(path)

    # Use mdfind (Spotlight) to search for Blender.app
    click.echo("  Ўъ Searching with Spotlight (mdfind)...")
    try:
        result = subprocess.run(
            ["mdfind", "-name", "Blender.app"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Get first result
            app_path = result.stdout.strip().split("\n")[0]
            blender_exe = Path(app_path) / "Contents/MacOS/Blender"
            if blender_exe.exists():
                return str(blender_exe)
    except Exception:
        pass

    return None


def find_blender_executable_windows() -> str | None:
    """Find Blender executable on Windows using registry and common paths."""
    if winreg is None:
        click.echo("  Ўъ Windows registry module not available")
        return None

    click.echo("  Ўъ Searching Windows Registry for Blender 4.x installations...")

    # First try registry search (most reliable for MSI installations)
    blender_paths = []
    uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

    for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for arch_key in [0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                with winreg.OpenKey(
                    hkey, uninstall_key_path, 0, winreg.KEY_READ | arch_key
                ) as uninstall_key:
                    for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                if (
                                    "blender" in display_name.lower()
                                    and display_version.startswith("4.")
                                ):
                                    install_location = winreg.QueryValueEx(
                                        subkey, "InstallLocation"
                                    )[0]
                                    if install_location:
                                        blender_exe = Path(install_location) / "blender.exe"
                                        if blender_exe.exists():
                                            click.echo(
                                                f"  Ўъ Found {display_name} {display_version} at: {install_location}"
                                            )
                                            return str(blender_exe)
                                        blender_paths.append(install_location)
                            except OSError:
                                continue
            except OSError:
                continue

    # If registry search found paths but no valid executable, show them
    if blender_paths:
        click.echo("  Ўъ Found installation paths in registry but no valid blender.exe:")
        for path in set(blender_paths):
            click.echo(f"    - {path}")

    # Try common installation paths as fallback
    click.echo("  Ўъ Checking common installation locations...")
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
            click.echo(f"  Ўъ Found Blender at: {path}")
            return str(path)

    # Try to find via Windows PATH
    click.echo("  Ўъ Checking if blender.exe is in system PATH...")
    try:
        result = subprocess.run(
            ["where", "blender"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            blender_exe_str = result.stdout.strip().split("\n")[0]
            if Path(blender_exe_str).exists():
                click.echo(f"  Ўъ Found Blender in PATH: {blender_exe_str}")
                return blender_exe_str
    except Exception:
        pass

    return None


def detect_blender_info(blender_path: str | Path) -> dict[str, Any]:
    """Detect Blender version and paths using Blender's Python APIs."""
    blender_path_obj = Path(blender_path)

    if not blender_path_obj.exists():
        raise click.ClickException(f"Blender executable not found: {blender_path_obj}")

    click.echo(f"Detecting Blender info: {blender_path_obj}")
    click.echo("  Ўъ Creating detection script...")

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
        temp_fd, temp_script = tempfile.mkstemp(suffix=".py", text=True)
        with os.fdopen(temp_fd, "w") as f:
            f.write(detection_script)

        click.echo("  Ўъ Starting Blender in background mode (this may take a moment)...")
        result = subprocess.run(
            [
                str(blender_path_obj),
                "--background",
                "--factory-startup",
                "--python",
                temp_script,
            ],
            capture_output=True,
            text=True,
            timeout=DETECT_BLENDER_INFO_TIMEOUT_SECONDS,
        )
        click.echo("  Ўъ Blender execution completed, processing results...")

        if result.returncode != 0:
            raise click.ClickException(f"Blender detection script failed: {result.stderr}")

        # Parse JSON output (extract JSON from mixed output)
        try:
            # Look for JSON in the output (it should be the last valid JSON block)
            lines = result.stdout.strip().split("\n")
            json_lines = []
            in_json = False

            for line in lines:
                if line.strip().startswith("{") and not in_json:
                    in_json = True
                    json_lines = [line]
                elif in_json:
                    json_lines.append(line)
                    if line.strip() == "}":
                        # Try to parse this JSON block
                        try:
                            json_text = "\n".join(json_lines)
                            detection_data = json.loads(json_text)
                            break
                        except json.JSONDecodeError:
                            # Continue looking for valid JSON
                            continue
            else:
                # No valid JSON found
                raise click.ClickException(
                    f"No valid JSON found in Blender output. Raw output: {result.stdout}"
                )

        except json.JSONDecodeError as e:
            raise click.ClickException(
                f"Failed to parse Blender detection output: {e}\nOutput: {result.stdout}"
            ) from e

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
                        test_file = os.path.join(path, ".test_write")
                        with open(test_file, "w") as f:
                            f.write("test")
                        os.remove(test_file)
                        plugin_dir = path
                        click.echo(f"Using writable addon directory: {plugin_dir}")
                        break
                    except OSError:
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
            click.echo("Searched paths:")
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
        root_dir_str = str(blender_path_obj.parent)

        # Show searched paths summary
        click.echo("Searched paths:")
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
            "root_dir": root_dir_str,
            "plugin_dir": str(plugin_dir),
            "user_addons": user_addons,
            "all_addon_paths": all_addon_paths,
            "extensions_dir": extensions_dir,
        }

    except subprocess.TimeoutExpired:
        raise click.ClickException(
            "Timeout while detecting Blender info. "
            "Blender may take longer to start on the first run. "
            "You can retry this command or set BLENDER_REMOTE_DETECT_TIMEOUT to a higher value."
        )
    except Exception as e:
        raise click.ClickException(f"Error detecting Blender info: {e}") from e
    finally:
        # Clean up temporary file
        if temp_script and os.path.exists(temp_script):
            try:
                os.unlink(temp_script)
            except OSError:
                pass  # Ignore cleanup errors

