"""Enhanced command-line interface for blender-remote using click.

This CLI provides comprehensive blender-remote management functionality.
The main entry point (uvx blender-remote) starts the MCP server.

Platform Support:
- Windows: Full support with automatic Blender path detection
- Linux: Full support with automatic Blender path detection
- macOS: Full support with automatic Blender path detection
- Cross-platform compatibility maintained throughout
"""

from __future__ import annotations

import click

from blender_remote.cli.commands.addon import addon
from blender_remote.cli.commands.config_group import config
from blender_remote.cli.commands.debug import debug
from blender_remote.cli.commands.execute import execute
from blender_remote.cli.commands.export import export
from blender_remote.cli.commands.init import init
from blender_remote.cli.commands.install import install
from blender_remote.cli.commands.pkg import pkg
from blender_remote.cli.commands.start import start
from blender_remote.cli.commands.status import status


@click.group()
@click.version_option(package_name="blender-remote")
def cli() -> None:
    """Top-level command group for blender-remote.

    Provides subcommands for configuring Blender, starting services, running code,
    and debugging integrations. Usually invoked via the ``blender-remote-cli`` entrypoint.
    """


cli.add_command(init)
cli.add_command(install)
cli.add_command(addon)
cli.add_command(config)
cli.add_command(export)
cli.add_command(start)
cli.add_command(execute)
cli.add_command(status)
cli.add_command(debug)
cli.add_command(pkg)


if __name__ == "__main__":
    cli()
