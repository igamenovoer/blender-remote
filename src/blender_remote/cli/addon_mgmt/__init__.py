"""Local Blender add-on management helpers for `blender-remote-cli addon ...`.

This package contains utilities for managing Blender **user add-ons** for a
local Blender installation. It intentionally avoids any network access and
operates by combining:

- one-shot Blender background runs for operations that require `bpy` /
  `addon_utils` (list/info/enable/disable/install),
- local filesystem operations for destructive actions (uninstall removal).
"""

from __future__ import annotations

from blender_remote.cli.addon_mgmt.fs import (
    is_path_within,
    remove_addon_target,
    resolve_addon_removal_target,
)
from blender_remote.cli.addon_mgmt.scripts import (
    build_addon_info_script,
    build_addon_list_script,
    build_addon_paths_script,
    build_addon_resolve_script,
    build_disable_addon_script,
    build_enable_addon_script,
    build_install_addon_script,
)

__all__ = [
    "build_addon_info_script",
    "build_addon_list_script",
    "build_addon_paths_script",
    "build_addon_resolve_script",
    "build_disable_addon_script",
    "build_enable_addon_script",
    "build_install_addon_script",
    "is_path_within",
    "remove_addon_target",
    "resolve_addon_removal_target",
]
