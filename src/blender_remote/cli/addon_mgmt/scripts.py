"""Blender-side script builders for `blender-remote-cli addon ...`.

This module generates small Python programs intended to be executed inside
Blender via `--background --python <script.py>`. Each script prints a JSON value
between sentinel markers so the CLI can reliably extract machine-readable
output even when Blender emits log noise.
"""

from __future__ import annotations

import textwrap

from blender_remote.cli.pkg.blender_background import (
    JSON_BEGIN_SENTINEL,
    JSON_END_SENTINEL,
)


def build_addon_paths_script() -> str:
    """Build a Blender script that reports add-on search paths.

    Returns
    -------
    str
        Blender-executed Python script that prints a JSON object containing the
        user add-ons directory and add-on search paths.
    """
    return textwrap.dedent(
        f"""
        import json
        import os

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
        addon_paths = []
        try:
            addon_paths = list(addon_utils.paths())
        except Exception:
            addon_paths = []

        data = {{
            "user_addons": user_addons,
            "addon_paths": addon_paths,
        }}

        _emit(data)
        """
    ).lstrip()


def build_addon_list_script(*, include_all: bool) -> str:
    """Build a Blender script that lists add-ons and their state.

    Parameters
    ----------
    include_all : bool
        If True, include add-ons from all search paths. If False, only include
        add-ons located inside the user add-ons directory.

    Returns
    -------
    str
        Blender-executed Python script that prints a JSON array.
    """
    return textwrap.dedent(
        f"""
        import json
        import os

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}
        INCLUDE_ALL = {include_all!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        def _norm(path):
            if not path:
                return None
            try:
                return os.path.normcase(os.path.abspath(path))
            except Exception:
                return path


        def _is_within(child, parent):
            if not child or not parent:
                return False
            try:
                return os.path.commonpath([child, parent]) == parent
            except Exception:
                return False


        def _source_for(path_norm, user_addons_norm, system_norm):
            if not path_norm:
                return "unknown"
            if user_addons_norm and _is_within(path_norm, user_addons_norm):
                return "user"
            if system_norm and _is_within(path_norm, system_norm):
                return "bundled"
            return "system"


        try:
            bpy.ops.wm.read_userpref()
        except Exception:
            pass

        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
        user_addons_norm = _norm(user_addons)
        system_root_norm = _norm(bpy.utils.resource_path("SYSTEM"))

        mods = addon_utils.modules(refresh=True)
        out = []
        for mod in mods:
            name = getattr(mod, "__name__", None)
            if not name:
                continue
            enabled, loaded = addon_utils.check(name)
            try:
                bl_info = addon_utils.module_bl_info(mod)
            except Exception:
                bl_info = {{}}

            mod_file = getattr(mod, "__file__", None)
            mod_file_norm = _norm(mod_file)

            if not INCLUDE_ALL and user_addons_norm:
                if not _is_within(mod_file_norm, user_addons_norm):
                    continue

            out.append(
                {{
                    "name": name,
                    "enabled": bool(enabled),
                    "loaded": bool(loaded),
                    "version": bl_info.get("version"),
                    "path": mod_file,
                    "source": _source_for(mod_file_norm, user_addons_norm, system_root_norm),
                }}
            )

        _emit(out)
        """
    ).lstrip()


def build_addon_info_script(*, addon_name: str) -> str:
    """Build a Blender script that reports detailed info for one add-on.

    Parameters
    ----------
    addon_name : str
        Add-on module name.

    Returns
    -------
    str
        Blender-executed Python script that prints a JSON object (or `{}` when
        not found).
    """
    return textwrap.dedent(
        f"""
        import json
        import os

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}
        ADDON_NAME = {addon_name!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        def _norm(path):
            if not path:
                return None
            try:
                return os.path.normcase(os.path.abspath(path))
            except Exception:
                return path


        def _is_within(child, parent):
            if not child or not parent:
                return False
            try:
                return os.path.commonpath([child, parent]) == parent
            except Exception:
                return False


        def _source_for(path_norm, user_addons_norm, system_norm):
            if not path_norm:
                return "unknown"
            if user_addons_norm and _is_within(path_norm, user_addons_norm):
                return "user"
            if system_norm and _is_within(path_norm, system_norm):
                return "bundled"
            return "system"


        try:
            bpy.ops.wm.read_userpref()
        except Exception:
            pass

        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
        user_addons_norm = _norm(user_addons)
        system_root_norm = _norm(bpy.utils.resource_path("SYSTEM"))

        for mod in addon_utils.modules(refresh=True):
            name = getattr(mod, "__name__", None)
            if name != ADDON_NAME:
                continue

            enabled, loaded = addon_utils.check(name)
            try:
                bl_info = addon_utils.module_bl_info(mod)
            except Exception:
                bl_info = {{}}

            mod_file = getattr(mod, "__file__", None)
            mod_file_norm = _norm(mod_file)

            info = {{
                "name": name,
                "enabled": bool(enabled),
                "loaded": bool(loaded),
                "version": bl_info.get("version"),
                "path": mod_file,
                "source": _source_for(mod_file_norm, user_addons_norm, system_root_norm),
                "author": bl_info.get("author"),
                "description": bl_info.get("description"),
                "category": bl_info.get("category"),
                "warning": bl_info.get("warning"),
                "doc_url": bl_info.get("doc_url"),
                "tracker_url": bl_info.get("tracker_url"),
            }}
            _emit(info)
            raise SystemExit(0)

        _emit({{}})
        """
    ).lstrip()


def build_addon_resolve_script(*, addon_name: str) -> str:
    """Build a Blender script that resolves an add-on module to its filesystem path.

    This is intended for uninstall safety checks and returns the resolved
    `__file__` plus the user add-ons directory.

    Parameters
    ----------
    addon_name : str
        Add-on module name.

    Returns
    -------
    str
        Blender-executed Python script that prints a JSON object.
    """
    return textwrap.dedent(
        f"""
        import json
        import os

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}
        ADDON_NAME = {addon_name!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        try:
            bpy.ops.wm.read_userpref()
        except Exception:
            pass

        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
        for mod in addon_utils.modules(refresh=True):
            name = getattr(mod, "__name__", None)
            if name != ADDON_NAME:
                continue
            enabled, loaded = addon_utils.check(name)
            _emit(
                {{
                    "found": True,
                    "module_name": name,
                    "enabled": bool(enabled),
                    "loaded": bool(loaded),
                    "file_path": getattr(mod, "__file__", None),
                    "user_addons": user_addons,
                }}
            )
            raise SystemExit(0)

        _emit(
            {{
                "found": False,
                "module_name": ADDON_NAME,
                "enabled": False,
                "loaded": False,
                "file_path": None,
                "user_addons": user_addons,
            }}
        )
        """
    ).lstrip()


def build_enable_addon_script(*, addon_name: str) -> str:
    """Build a Blender script that enables an add-on and saves preferences."""
    return _build_toggle_script(op="enable", addon_name=addon_name)


def build_disable_addon_script(*, addon_name: str) -> str:
    """Build a Blender script that disables an add-on and saves preferences."""
    return _build_toggle_script(op="disable", addon_name=addon_name)


def _build_toggle_script(*, op: str, addon_name: str) -> str:
    op_normalized = (op or "").lower()
    if op_normalized not in {"enable", "disable"}:
        raise ValueError(f"Unknown op: {op!r}")

    return textwrap.dedent(
        f"""
        import json
        import traceback

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}
        OP = {op_normalized!r}
        ADDON_NAME = {addon_name!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        try:
            bpy.ops.wm.read_userpref()
        except Exception:
            pass

        try:
            if OP == "enable":
                addon_utils.enable(ADDON_NAME, default_set=True, persistent=True)
            else:
                addon_utils.disable(ADDON_NAME, default_set=True, persistent=True)

            try:
                bpy.ops.wm.save_userpref()
            except Exception:
                pass

            enabled, loaded = addon_utils.check(ADDON_NAME)
            _emit({{"op": OP, "module_name": ADDON_NAME, "enabled": bool(enabled), "loaded": bool(loaded)}})
        except Exception as exc:
            _emit(
                {{
                    "op": OP,
                    "module_name": ADDON_NAME,
                    "enabled": False,
                    "loaded": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }}
            )
        """
    ).lstrip()


def build_install_addon_script(
    *, source_path: str, overwrite: bool, enable: bool
) -> str:
    """Build a Blender script that installs an add-on from a local source.

    Parameters
    ----------
    source_path : str
        Local filesystem path (directory, `.zip`, or `.py` file).
    overwrite : bool
        Whether to overwrite an existing add-on with the same ID.
    enable : bool
        Whether to enable the add-on after installing.

    Returns
    -------
    str
        Blender-executed Python script that prints a JSON object.
    """
    return textwrap.dedent(
        f"""
        import json
        import os
        import shutil
        import traceback
        import zipfile

        import bpy
        import addon_utils

        BEGIN = {JSON_BEGIN_SENTINEL!r}
        END = {JSON_END_SENTINEL!r}
        SOURCE = {source_path!r}
        OVERWRITE = {overwrite!r}
        ENABLE = {enable!r}


        def _emit(data):
            print(BEGIN)
            print(json.dumps(data, ensure_ascii=True))
            print(END)


        def _zip_guess_module_name(path):
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    names = [n for n in zf.namelist() if n and not n.endswith("/")]
            except Exception:
                return None

            top = set()
            for name in names:
                first = name.split("/", 1)[0]
                if first:
                    top.add(first)

            if len(top) != 1:
                return None

            candidate = next(iter(top))
            if candidate.lower().endswith(".py"):
                return os.path.splitext(candidate)[0]
            return candidate


        errors = []
        warnings = []
        module_name = None
        installed_path = None
        enabled = False

        try:
            source_abs = os.path.abspath(SOURCE)
            if not os.path.exists(source_abs):
                raise FileNotFoundError(source_abs)

            try:
                bpy.ops.wm.read_userpref()
            except Exception:
                pass

            if os.path.isdir(source_abs):
                user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
                if not user_addons:
                    raise RuntimeError("Could not resolve user add-ons directory")

                module_name = os.path.basename(os.path.normpath(source_abs))
                dest_dir = os.path.join(user_addons, module_name)
                installed_path = dest_dir

                if os.path.exists(dest_dir):
                    if not OVERWRITE:
                        raise FileExistsError(dest_dir)
                    shutil.rmtree(dest_dir)

                shutil.copytree(source_abs, dest_dir)
                try:
                    addon_utils.modules(refresh=True)
                except Exception:
                    pass

                if ENABLE:
                    addon_utils.enable(module_name, default_set=True, persistent=True)
                    try:
                        bpy.ops.wm.save_userpref()
                    except Exception:
                        pass
                    enabled = bool(addon_utils.check(module_name)[0])

                _emit(
                    {{
                        "op": "install",
                        "source": source_abs,
                        "module_name": module_name,
                        "installed_path": installed_path,
                        "enabled": bool(enabled),
                        "warnings": warnings,
                        "errors": errors,
                    }}
                )
                raise SystemExit(0)

            ext = os.path.splitext(source_abs)[1].lower()
            if ext not in {{".zip", ".py"}}:
                raise ValueError(f"Unsupported add-on source: {{source_abs}}")

            before = {{m.__name__ for m in addon_utils.modules(refresh=True)}}
            bpy.ops.preferences.addon_install(
                filepath=source_abs,
                overwrite=OVERWRITE,
                enable_on_install=ENABLE,
            )
            try:
                bpy.ops.preferences.addon_refresh()
            except Exception:
                pass

            after_mods = addon_utils.modules(refresh=True)
            after = {{m.__name__ for m in after_mods}}
            added = sorted(after - before)

            if len(added) == 1:
                module_name = added[0]
            elif ext == ".py":
                module_name = os.path.splitext(os.path.basename(source_abs))[0]
            elif ext == ".zip":
                module_name = _zip_guess_module_name(source_abs)

            if module_name:
                for mod in after_mods:
                    if getattr(mod, "__name__", None) == module_name:
                        installed_path = getattr(mod, "__file__", None)
                        break

            if ENABLE and module_name:
                try:
                    bpy.ops.wm.save_userpref()
                except Exception:
                    pass
                enabled = bool(addon_utils.check(module_name)[0])

            _emit(
                {{
                    "op": "install",
                    "source": source_abs,
                    "module_name": module_name,
                    "installed_path": installed_path,
                    "enabled": bool(enabled),
                    "warnings": warnings,
                    "errors": errors,
                }}
            )
        except Exception as exc:
            errors.append(str(exc))
            _emit(
                {{
                    "op": "install",
                    "source": SOURCE,
                    "module_name": module_name,
                    "installed_path": installed_path,
                    "enabled": bool(enabled),
                    "warnings": warnings,
                    "errors": errors,
                    "traceback": traceback.format_exc(),
                }}
            )
        """
    ).lstrip()
