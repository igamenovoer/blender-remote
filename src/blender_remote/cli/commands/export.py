from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import click

from ..addon import get_addon_zip_path
from ..scripts import KEEPALIVE_SCRIPT


def export_addon(output_dir: Path) -> None:
    """Exports the addon source to the specified directory."""
    try:
        addon_zip_path = get_addon_zip_path()
        click.echo(f"  Ўъ Found addon zip at {addon_zip_path}")

        # Unpack to the target directory. This will create a 'bld_remote_mcp' subdir.
        shutil.unpack_archive(addon_zip_path, output_dir)

        click.echo(f"  Ўъ Extracted addon to {output_dir / 'bld_remote_mcp'}")

    except Exception as e:
        raise click.ClickException(f"Failed to export addon: {e}") from e


def export_keep_alive_script(output_dir: Path) -> None:
    """Exports the keep-alive script to the specified directory."""
    script_path = output_dir / "keep-alive.py"
    with open(script_path, "w", encoding="utf-8") as f:
        # Dedent the script to remove leading whitespace from the multiline string
        f.write(textwrap.dedent(KEEPALIVE_SCRIPT).strip())
    click.echo(f"  Ўъ Wrote keep-alive script to {script_path}")


@click.command()
@click.option(
    "--content",
    type=click.Choice(["addon", "keep-alive.py"]),
    required=True,
    help="Content to export: 'addon' or 'keep-alive.py'",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    required=True,
    help="Output directory to export content to.",
)
def export(content: str, output_dir: str) -> None:
    """Export addon source code or keep-alive script.

    Parameters
    ----------
    content:
        Either ``\"addon\"`` to export the ``bld_remote_mcp`` addon sources, or
        ``\"keep-alive.py\"`` to export the keep-alive helper script.
    output_dir:
        Target directory where the selected content will be written.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"Exporting '{content}' to '{output_dir}'...")

    if content == "addon":
        export_addon(output_path)
    elif content == "keep-alive.py":
        export_keep_alive_script(output_path)

    click.echo(f"Successfully exported '{content}' to '{output_dir}'")

