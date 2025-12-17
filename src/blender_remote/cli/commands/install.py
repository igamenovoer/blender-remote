from __future__ import annotations

import os
import platform
import subprocess
import tempfile

import click

from ..addon import build_addon_install_script, get_addon_zip_path
from ..config import BlenderRemoteConfig
from ..constants import CONFIG_FILE, DEFAULT_PORT
from ..detection import (
    detect_blender_info,
    find_blender_executable_macos,
    find_blender_executable_windows,
)


@click.command()
def install() -> None:
    """Install the ``bld_remote_mcp`` addon into Blender.

    If no configuration exists yet, attempts to auto-detect a suitable Blender
    installation (on Windows and macOS) and then writes configuration pointing
    at the selected executable and addon directory.

    This command is typically run once per environment, or after upgrading Blender.
    """
    click.echo("[INSTALL] Installing bld_remote_mcp addon...")

    # Try to load existing config
    config = BlenderRemoteConfig()
    blender_config = None
    blender_path = None
    cli_timeout_seconds = 300.0

    try:
        blender_config = config.get("blender")
        if blender_config:
            blender_path = blender_config.get("exec_path")
    except click.ClickException:
        # Config file doesn't exist
        pass

    try:
        cli_timeout_value = config.get("cli.timeout_sec")
    except click.ClickException:
        cli_timeout_value = None

    if cli_timeout_value is not None:
        try:
            parsed_timeout = float(cli_timeout_value)
        except (TypeError, ValueError):
            parsed_timeout = None

        if parsed_timeout is not None and parsed_timeout > 0:
            cli_timeout_seconds = parsed_timeout

    # If no config or no blender path, try auto-detection
    if not blender_config or not blender_path:
        current_platform = platform.system()

        if current_platform == "Windows":
            click.echo("[AUTO-DETECT] Attempting to auto-detect Blender on Windows...")
            detected_path = find_blender_executable_windows()

            if detected_path:
                click.echo(f"[FOUND] Blender found at: {detected_path}")
                use_detected = click.confirm("Use this detected path?", default=True)

                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True),
                    )
            else:
                click.echo("[NOT FOUND] Could not auto-detect Blender on Windows")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True),
                )
        elif current_platform == "Darwin":  # macOS
            click.echo("[AUTO-DETECT] Attempting to auto-detect Blender on macOS...")
            detected_path = find_blender_executable_macos()

            if detected_path:
                click.echo(f"[FOUND] Blender found at: {detected_path}")
                use_detected = click.confirm("Use this detected path?", default=True)

                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True),
                    )
            else:
                click.echo("[NOT FOUND] Could not auto-detect Blender on macOS")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True),
                )
        else:
            # For other platforms, prompt for path
            click.echo("[MANUAL] Please enter your Blender executable path:")
            blender_path = click.prompt(
                "Path to Blender executable",
                type=click.Path(exists=True),
            )

    # If we got a blender path, detect its info and save config
    if blender_path:
        click.echo(f"[CONFIG] Analyzing Blender installation at: {blender_path}")
        try:
            blender_info = detect_blender_info(blender_path)

            # Create and save config
            new_config = {
                "blender": blender_info,
                "cli": {"timeout_sec": cli_timeout_seconds},
                "mcp_service": {"default_port": DEFAULT_PORT, "log_level": "INFO"},
            }

            config.save(new_config)
            click.echo(f"[CONFIG] Configuration saved to: {CONFIG_FILE}")
            blender_config = blender_info

        except Exception as e:
            raise click.ClickException(
                f"Failed to analyze Blender installation: {e}"
            ) from e
    else:
        raise click.ClickException("No Blender executable path provided")

    # Get addon zip path
    addon_zip = get_addon_zip_path()

    click.echo(f"[ADDON] Using addon: {addon_zip}")

    # Create Python script for addon installation
    # Use as_posix() to ensure forward slashes on all platforms
    addon_zip_posix = addon_zip.as_posix()
    install_script = build_addon_install_script(addon_zip_posix, "bld_remote_mcp")

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
            timeout=cli_timeout_seconds,
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
