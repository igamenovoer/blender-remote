from __future__ import annotations

from typing import Any

import click
from omegaconf import OmegaConf

from ..config import BlenderRemoteConfig


@click.group()
def config() -> None:
    """Manage blender-remote configuration values.

    This group exposes subcommands for reading and updating the YAML configuration
    managed by :class:`BlenderRemoteConfig`, such as the Blender executable path
    and MCP service settings.
    """


@config.command()
@click.argument("key_value", required=False)
def set(key_value: str | None) -> None:
    """Set a configuration value using ``key=value`` syntax.

    Parameters
    ----------
    key_value:
        String in the form ``\"section.key=value\"``. The value is parsed into
        ``int``, ``float``, or ``bool`` where possible; otherwise it is stored
        as a string.
    """
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
    """Get one or all configuration values.

    Parameters
    ----------
    key:
        Optional dot-notation key (for example ``\"blender.exec_path\"``). If
        omitted, the full configuration is printed as YAML.
    """
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

