"""`blender-remote-cli addon` command group.

This module provides local user add-on management for a configured Blender
installation. Operations that require `bpy` / `addon_utils` run Blender in
background mode; uninstall performs local filesystem removal with safety checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from blender_remote.cli.addon_mgmt import (
    build_addon_info_script,
    build_addon_list_script,
    build_addon_paths_script,
    build_addon_resolve_script,
    build_disable_addon_script,
    build_enable_addon_script,
    build_install_addon_script,
    is_path_within,
    remove_addon_target,
    resolve_addon_removal_target,
)
from blender_remote.cli.pkg.blender_background import (
    get_cli_timeout_seconds,
    get_configured_blender_executable,
    run_blender_background_json,
    run_blender_background_json_value,
)


@click.group()
def addon() -> None:
    """Manage Blender user add-ons for a local installation."""


def _echo_json(value: Any) -> None:
    click.echo(json.dumps(value, ensure_ascii=True))


@addon.command("paths")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def paths(json_output: bool) -> None:
    """Show discovered add-on paths for the configured Blender executable.

    Parameters
    ----------
    json_output : bool
        If True, print a single JSON object to stdout.
    """
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    data = run_blender_background_json(
        blender_executable=blender_executable,
        python_script=build_addon_paths_script(),
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )
    data["blender_executable"] = str(blender_executable)

    if json_output:
        _echo_json(data)
        return

    click.echo(f"Blender executable: {blender_executable}")
    click.echo(f"User add-ons directory: {data.get('user_addons')}")
    click.echo("Add-on search paths:")
    addon_paths = data.get("addon_paths")
    if isinstance(addon_paths, list):
        for entry in addon_paths:
            click.echo(f"- {entry}")


@addon.command("list")
@click.option("--all", "include_all", is_flag=True, help="Include all add-ons")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON array to stdout (no extra text)",
)
def list_cmd(include_all: bool, json_output: bool) -> None:
    """List installed add-ons and their enablement state.

    Parameters
    ----------
    include_all : bool
        If True, include add-ons from all search paths. Otherwise list user
        add-ons only.
    json_output : bool
        If True, print a single JSON array to stdout.
    """
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    result = run_blender_background_json_value(
        blender_executable=blender_executable,
        python_script=build_addon_list_script(include_all=include_all),
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )

    if not isinstance(result, list):
        raise click.ClickException("Expected addon list script to return a JSON array.")

    result_sorted = sorted(
        (entry for entry in result if isinstance(entry, dict)),
        key=lambda entry: str(entry.get("name") or ""),
    )

    if json_output:
        _echo_json(result_sorted)
        return

    for entry in result_sorted:
        name = entry.get("name")
        enabled = entry.get("enabled")
        source = entry.get("source")
        click.echo(f"{name} (enabled={enabled}, source={source})")


@addon.command("info")
@click.argument("addon_name", required=True)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def info(addon_name: str, json_output: bool) -> None:
    """Show details for one add-on.

    Parameters
    ----------
    addon_name : str
        Add-on module name.
    json_output : bool
        If True, print a single JSON object to stdout.
    """
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    data = run_blender_background_json(
        blender_executable=blender_executable,
        python_script=build_addon_info_script(addon_name=addon_name),
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )

    if not data:
        if json_output:
            _echo_json({})
        raise click.ClickException(f"Add-on not found: {addon_name}")

    if json_output:
        _echo_json(data)
        return

    click.echo(f"Name: {data.get('name')}")
    click.echo(f"Enabled: {data.get('enabled')}")
    click.echo(f"Loaded: {data.get('loaded')}")
    click.echo(f"Version: {data.get('version')}")
    click.echo(f"Source: {data.get('source')}")
    click.echo(f"Path: {data.get('path')}")
    if data.get("description"):
        click.echo(f"Description: {data.get('description')}")
    if data.get("author"):
        click.echo(f"Author: {data.get('author')}")
    if data.get("category"):
        click.echo(f"Category: {data.get('category')}")


@addon.command("enable")
@click.argument("addon_name", required=True)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def enable(addon_name: str, json_output: bool) -> None:
    """Enable an add-on and persist preferences."""
    _toggle(addon_name=addon_name, op="enable", json_output=json_output)


@addon.command("disable")
@click.argument("addon_name", required=True)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def disable(addon_name: str, json_output: bool) -> None:
    """Disable an add-on and persist preferences."""
    _toggle(addon_name=addon_name, op="disable", json_output=json_output)


def _toggle(*, addon_name: str, op: str, json_output: bool) -> None:
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    if op == "enable":
        script = build_enable_addon_script(addon_name=addon_name)
    elif op == "disable":
        script = build_disable_addon_script(addon_name=addon_name)
    else:
        raise click.ClickException(f"Unknown operation: {op!r}")

    data = run_blender_background_json(
        blender_executable=blender_executable,
        python_script=script,
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )

    if data.get("error"):
        if json_output:
            _echo_json(data)
        raise click.ClickException(str(data.get("error")))

    if json_output:
        _echo_json(data)
        return

    click.echo(f"{op}: {addon_name} -> enabled={data.get('enabled')}")


@addon.command("install")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
)
@click.option("--enable", is_flag=True, help="Enable after installing")
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite an existing add-on with the same ID",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def install(source: Path, enable: bool, overwrite: bool, json_output: bool) -> None:
    """Install an add-on from a local folder, `.zip`, or `.py` file."""
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    data = run_blender_background_json(
        blender_executable=blender_executable,
        python_script=build_install_addon_script(
            source_path=str(source), overwrite=overwrite, enable=enable
        ),
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )

    errors = data.get("errors") if isinstance(data.get("errors"), list) else []
    if errors:
        if json_output:
            _echo_json(data)
        raise click.ClickException(str(errors[0]))

    if json_output:
        _echo_json(data)
        return

    click.echo(
        f"Installed {data.get('module_name')} (enabled={data.get('enabled')}) at {data.get('installed_path')}"
    )


@addon.command("uninstall")
@click.argument("addon_name", required=True)
@click.option(
    "--force",
    is_flag=True,
    help="Allow uninstall outside the user add-ons directory (dangerous)",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def uninstall(addon_name: str, force: bool, json_output: bool) -> None:
    """Disable an add-on (best-effort) and remove its files from disk."""
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    resolved = run_blender_background_json(
        blender_executable=blender_executable,
        python_script=build_addon_resolve_script(addon_name=addon_name),
        timeout_seconds=timeout_seconds,
        factory_startup=False,
    )

    uninstall_result: dict[str, Any] = {
        "op": "uninstall",
        "module_name": addon_name,
        "disabled": False,
        "removed": False,
        "removed_path": None,
    }

    if not resolved.get("found"):
        if json_output:
            _echo_json(uninstall_result)
        raise click.ClickException(f"Add-on not found: {addon_name}")

    file_path = resolved.get("file_path")
    user_addons = resolved.get("user_addons")
    if not file_path or not user_addons:
        if json_output:
            _echo_json(uninstall_result)
        raise click.ClickException("Could not resolve add-on file path for uninstall.")

    addon_file = Path(str(file_path))
    user_addons_dir = Path(str(user_addons))
    target = resolve_addon_removal_target(addon_file_path=addon_file)

    if not force and not is_path_within(child=target, parent=user_addons_dir):
        if json_output:
            _echo_json(uninstall_result)
        raise click.ClickException(
            "Refusing to uninstall an add-on outside the user add-ons directory. "
            "Re-run with --force to override."
        )

    disabled = False
    try:
        disable_result = run_blender_background_json(
            blender_executable=blender_executable,
            python_script=build_disable_addon_script(addon_name=addon_name),
            timeout_seconds=timeout_seconds,
            factory_startup=False,
        )
        if not disable_result.get("error"):
            disabled = not bool(disable_result.get("enabled"))
    except click.ClickException:
        disabled = False

    try:
        remove_addon_target(target_path=target)
    except Exception as exc:
        uninstall_result.update({"disabled": disabled, "removed": False})
        if json_output:
            _echo_json(uninstall_result)
        raise click.ClickException(f"Failed to remove add-on files: {exc}") from exc

    uninstall_result.update(
        {
            "disabled": disabled,
            "removed": True,
            "removed_path": str(target),
        }
    )

    if json_output:
        _echo_json(uninstall_result)
        return

    click.echo(f"Removed {addon_name}: {target}")
