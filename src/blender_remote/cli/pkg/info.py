"""Blender Python environment inspection for packaging decisions.

This module backs `blender-remote-cli pkg info` and provides a JSON snapshot of
the local Blender/Python environment by running Blender in background mode.
"""

from __future__ import annotations

from typing import Any

from blender_remote.cli.pkg.blender_background import (
    JSON_BEGIN_SENTINEL,
    JSON_END_SENTINEL,
    get_cli_timeout_seconds,
    get_configured_blender_executable,
    run_blender_background_json,
)


def get_blender_python_info() -> dict[str, Any]:
    """Collect information about Blender's embedded Python environment.

    Returns
    -------
    dict[str, Any]
        JSON-serializable dictionary describing the local environment.
    """
    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    script = _build_info_script(blender_executable=str(blender_executable))
    return run_blender_background_json(
        blender_executable=blender_executable,
        python_script=script,
        timeout_seconds=timeout_seconds,
        factory_startup=True,
    )


def render_blender_python_info(info: dict[str, Any]) -> str:
    """Render `pkg info` JSON into a human-readable report.

    Parameters
    ----------
    info : dict[str, Any]
        JSON object returned by `get_blender_python_info`.

    Returns
    -------
    str
        Multi-line report suitable for console output.
    """
    blender = info.get("blender", {}) if isinstance(info.get("blender"), dict) else {}
    python = info.get("python", {}) if isinstance(info.get("python"), dict) else {}
    pip = info.get("pip", {}) if isinstance(info.get("pip"), dict) else {}
    site = info.get("site", {}) if isinstance(info.get("site"), dict) else {}

    lines: list[str] = []
    lines.append("Local Blender/Python environment:")
    lines.append(f"- Blender: {blender.get('version_string')}")
    lines.append(f"- Blender executable: {blender.get('executable')}")
    lines.append(
        f"- Python: {python.get('version_info', {}).get('major')}.{python.get('version_info', {}).get('minor')}.{python.get('version_info', {}).get('micro')}"
    )
    lines.append(f"- Platform: {python.get('platform')} ({python.get('machine')})")
    lines.append(f"- sysconfig platform: {python.get('sysconfig_platform')}")

    site_packages = site.get("site_packages")
    if isinstance(site_packages, list) and site_packages:
        lines.append("- site-packages:")
        for entry in site_packages:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            writable = entry.get("writable")
            exists = entry.get("exists")
            lines.append(f"  - {path} (exists={exists}, writable={writable})")

    user_site = site.get("user_site")
    if user_site:
        lines.append(f"- user-site: {user_site}")

    pip_version = pip.get("version")
    if pip.get("importable"):
        lines.append(f"- pip: {pip_version}")
    else:
        lines.append("- pip: not available (run `blender-remote-cli pkg bootstrap`)")

    suggested = info.get("suggested_pip_download")
    if isinstance(suggested, dict):
        lines.append("- suggested pip download flags:")
        args = []
        if suggested.get("platform"):
            args.extend(["--platform", str(suggested["platform"])])
        if suggested.get("python_version"):
            args.extend(["--python-version", str(suggested["python_version"])])
        if suggested.get("implementation"):
            args.extend(["--implementation", str(suggested["implementation"])])
        if suggested.get("only_binary"):
            args.extend(["--only-binary", str(suggested["only_binary"])])
        if args:
            lines.append(
                f"  python -m pip download -d ./wheelhouse {' '.join(args)} <PKG_SPEC...>"
            )

    return "\n".join(lines)


def _build_info_script(*, blender_executable: str) -> str:
    """Build a Blender background script that prints a sentinel-wrapped JSON object."""
    return rf"""
import json
import os
import platform
import site
import sys
import sysconfig
import tempfile

import bpy

BEGIN = {JSON_BEGIN_SENTINEL!r}
END = {JSON_END_SENTINEL!r}


def _is_writable(path: str) -> bool:
    try:
        return os.access(path, os.W_OK)
    except Exception:
        return False


def _guess_pip_platform_tag() -> str | None:
    sys_platform = sys.platform
    machine = platform.machine().lower()

    if sys_platform.startswith("win"):
        if machine in {{"amd64", "x86_64"}}:
            return "win_amd64"
        if machine in {{"x86", "i386", "i686"}}:
            return "win32"
        return "win_amd64"

    if sys_platform == "darwin":
        if machine in {{"arm64", "aarch64"}}:
            return "macosx_11_0_arm64"
        if machine in {{"x86_64", "amd64"}}:
            return "macosx_11_0_x86_64"
        return "macosx_11_0_x86_64"

    if sys_platform.startswith("linux"):
        if machine in {{"x86_64", "amd64"}}:
            return "manylinux2014_x86_64"
        if machine in {{"aarch64", "arm64"}}:
            return "manylinux2014_aarch64"
        return "manylinux2014_x86_64"

    return None


python_version_nodot = f"{{sys.version_info.major}}{{sys.version_info.minor}}"
platform_tag = _guess_pip_platform_tag()

site_packages: list[dict[str, object]] = []
try:
    for p in site.getsitepackages():
        site_packages.append(
            {{"path": p, "exists": os.path.isdir(p), "writable": _is_writable(p)}}
        )
except Exception:
    pass

user_site = None
try:
    user_site = site.getusersitepackages()
except Exception:
    user_site = None

pip_info: dict[str, object] = {{"importable": False, "version": None}}
try:
    import pip  # type: ignore

    pip_info["importable"] = True
    pip_info["version"] = getattr(pip, "__version__", None)
except Exception:
    pass

data = {{
    "blender": {{
        "version_string": getattr(bpy.app, "version_string", None),
        "version": getattr(bpy.app, "version", None),
        "executable": {blender_executable!r},
    }},
    "python": {{
        "version": sys.version,
        "version_info": {{
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
        }},
        "platform": sys.platform,
        "machine": platform.machine(),
        "sysconfig_platform": sysconfig.get_platform(),
        "tempdir": tempfile.gettempdir(),
    }},
    "site": {{
        "site_packages": site_packages,
        "user_site": user_site,
    }},
    "pip": pip_info,
    "suggested_pip_download": {{
        "python_version": python_version_nodot,
        "platform": platform_tag,
        "implementation": "cp",
        "only_binary": ":all:",
    }},
}}

print(BEGIN)
print(json.dumps(data, ensure_ascii=True))
print(END)
"""
