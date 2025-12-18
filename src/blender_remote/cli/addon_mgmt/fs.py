"""Filesystem utilities for local Blender add-on management.

The CLI enforces safety rules for uninstall operations by defaulting to removal
of add-ons located inside Blender's user add-ons directory.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def is_path_within(*, child: Path, parent: Path) -> bool:
    """Return True if `child` is located within `parent`.

    Parameters
    ----------
    child : pathlib.Path
        Candidate child path.
    parent : pathlib.Path
        Candidate parent directory.

    Returns
    -------
    bool
        True when `child` is within `parent`, otherwise False.
    """
    child_str = os.path.normcase(os.path.abspath(str(child)))
    parent_str = os.path.normcase(os.path.abspath(str(parent)))
    try:
        return os.path.commonpath([child_str, parent_str]) == parent_str
    except ValueError:
        return False


def resolve_addon_removal_target(*, addon_file_path: Path) -> Path:
    """Resolve the filesystem path that should be removed for an add-on.

    Parameters
    ----------
    addon_file_path : pathlib.Path
        The `__file__` path for the add-on module returned by Blender.

    Returns
    -------
    pathlib.Path
        Directory to remove for package add-ons, or the file to remove for
        single-file add-ons.
    """
    if addon_file_path.name == "__init__.py":
        return addon_file_path.parent
    return addon_file_path


def remove_addon_target(*, target_path: Path) -> None:
    """Remove an add-on file or directory from disk.

    Parameters
    ----------
    target_path : pathlib.Path
        Target file or directory to remove.

    Raises
    ------
    FileNotFoundError
        If the target does not exist.
    OSError
        If removal fails.
    """
    if not target_path.exists():
        raise FileNotFoundError(str(target_path))

    if target_path.is_dir():
        shutil.rmtree(target_path)
        return

    target_path.unlink()
