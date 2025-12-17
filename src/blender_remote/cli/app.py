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

from .commands.config_group import config
from .commands.debug import debug
from .commands.execute import execute
from .commands.export import export
from .commands.init import init
from .commands.install import install
from .commands.pkg import pkg
from .commands.start import start
from .commands.status import status


@click.group()
@click.version_option(version="1.2.2")
def cli() -> None:
    """Top-level command group for blender-remote.

    Provides subcommands for configuring Blender, starting services, running code,
    and debugging integrations. Usually invoked via the ``blender-remote-cli`` entrypoint.
    """


cli.add_command(init)
cli.add_command(install)
cli.add_command(config)
cli.add_command(export)
cli.add_command(start)
cli.add_command(execute)
cli.add_command(status)
cli.add_command(debug)
cli.add_command(pkg)


if __name__ == "__main__":
    cli()
