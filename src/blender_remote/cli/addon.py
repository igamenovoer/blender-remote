"""Addon packaging and installation helpers for the blender-remote CLI."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import click


def get_addon_zip_path() -> Path:
    """Get path to the addon zip file."""
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
        from importlib import resources as importlib_resources

        try:
            package_path = (
                importlib_resources.files("blender_remote") / "addon" / "bld_remote_mcp"
            )
            addon_dir = Path(str(package_path))
        except Exception:
            # Final fallback to pkg_resources
            try:
                import pkg_resources

                addon_dir = Path(
                    pkg_resources.resource_filename("blender_remote", "addon/bld_remote_mcp")
                )
            except Exception:
                addon_dir = None

        if addon_dir is not None and addon_dir.exists():
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
                str(addon_dir.parent),
                "bld_remote_mcp",
            )
            return addon_zip
    except Exception:
        pass

    raise click.ClickException("Could not find bld_remote_mcp addon files")


def get_debug_addon_zip_path() -> Path:
    """Get path to the debug addon zip file."""
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
        from importlib import resources as importlib_resources

        try:
            package_path = (
                importlib_resources.files("blender_remote")
                / "addon"
                / "simple-tcp-executor"
            )
            addon_dir = Path(str(package_path))
        except Exception:
            # Final fallback to pkg_resources
            try:
                import pkg_resources

                addon_dir = Path(
                    pkg_resources.resource_filename(
                        "blender_remote", "addon/simple-tcp-executor"
                    )
                )
            except Exception:
                addon_dir = None

        if addon_dir is not None and addon_dir.exists():
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
                str(addon_dir.parent),
                "simple-tcp-executor",
            )
            return addon_zip
    except Exception:
        pass

    raise click.ClickException("Could not find simple-tcp-executor addon files")


def build_addon_install_script(addon_zip_path_posix: str, addon_module_name: str) -> str:
    """Build the Blender-side Python script to install and enable an addon."""
    return f'''
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
addon_path = "{addon_zip_path_posix}"
addon_name = "{addon_module_name}"

install_and_enable_addon(addon_path, addon_name)
'''

