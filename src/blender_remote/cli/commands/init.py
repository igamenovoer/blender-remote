from __future__ import annotations

import platform
import shutil

import click
from omegaconf import OmegaConf

from ..config import BlenderRemoteConfig
from ..constants import CONFIG_FILE, DEFAULT_PORT
from ..detection import (
    detect_blender_info,
    find_blender_executable_macos,
    find_blender_executable_windows,
)


@click.command()
@click.argument("blender_path", type=click.Path(exists=True), required=False)
@click.option("--backup", is_flag=True, help="Create backup of existing config")
def init(blender_path: str | None, backup: bool) -> None:
    """Initialize blender-remote configuration.

    On macOS and Windows this will auto-detect Blender if ``blender_path`` is not
    provided; on other platforms the user is prompted for the executable path.

    Parameters
    ----------
    blender_path:
        Optional explicit path to the Blender executable. If omitted, the CLI
        attempts platform-specific auto-detection or prompts the user.
    backup:
        If ``True``, create a ``.yaml.bak`` backup of any existing configuration
        file before writing a new one.
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
                use_detected = click.confirm("Use this detected path?", default=True)

                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True),
                    )
            else:
                click.echo("Could not auto-detect Blender on macOS")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True),
                )
        elif current_platform == "Windows":  # Windows
            click.echo("Attempting to auto-detect Blender on Windows...")
            detected_path = find_blender_executable_windows()

            if detected_path:
                click.echo(f"Found Blender at: {detected_path}")
                use_detected = click.confirm("Use this detected path?", default=True)

                if use_detected:
                    blender_path = detected_path
                else:
                    blender_path = click.prompt(
                        "Please enter the path to your Blender executable",
                        type=click.Path(exists=True),
                    )
            else:
                click.echo("Could not auto-detect Blender on Windows")
                blender_path = click.prompt(
                    "Please enter the path to your Blender executable",
                    type=click.Path(exists=True),
                )
        else:
            # For other platforms, prompt for path
            blender_path = click.prompt(
                "Please enter the path to your Blender executable",
                type=click.Path(exists=True),
            )

    # Detect Blender info
    click.echo("\nAnalyzing Blender installation...")
    blender_info = detect_blender_info(blender_path)

    # Create config
    click.echo("  Ўъ Generating configuration structure...")
    config = {
        "blender": blender_info,
        "cli": {"timeout_sec": 300},
        "mcp_service": {"default_port": DEFAULT_PORT, "log_level": "INFO"},
    }

    # Save config
    click.echo("  Ўъ Saving configuration...")
    config_manager = BlenderRemoteConfig()
    config_manager.save(config)

    # Display final configuration (ASCII-only for cross-platform safety)
    click.echo(f"\n[OK] Configuration saved to: {CONFIG_FILE}")
    click.echo("\n[CONFIG] Generated configuration:")

    # Display the configuration like 'config get' does
    config_yaml = OmegaConf.to_yaml(config)
    click.echo(config_yaml)

    click.echo(
        "Initialization complete! You can now use other blender-remote-cli commands."
    )
