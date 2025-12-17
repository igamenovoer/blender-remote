"""Remote environment inspection for packaging decisions.

This module backs `blender-remote-cli pkg info` and provides a JSON snapshot of
the remote Blender/Python environment, including `sys.executable`,
`bpy.app.python_args`, site-packages locations, and basic network/pip status.
"""

from __future__ import annotations

from typing import Any

from blender_remote.cli.pkg.ports import resolve_mcp_port
from blender_remote.cli.pkg.remote_exec import execute_json


def get_remote_python_info(*, port: int | None) -> dict[str, Any]:
    """Collect information about the remote Blender/Python environment.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.

    Returns
    -------
    dict[str, Any]
        JSON-serializable dictionary describing the remote environment.
    """
    mcp_port = resolve_mcp_port(port)

    code = r"""
import json
import os
import platform
import site
import sys
import sysconfig
import tempfile
import time
import urllib.request

import bpy


def _is_writable(path: str) -> bool:
    try:
        return os.access(path, os.W_OK)
    except Exception:
        return False


def _guess_pip_platform_tag() -> str | None:
    sys_platform = sys.platform
    machine = platform.machine().lower()

    if sys_platform.startswith("win"):
        if machine in {"amd64", "x86_64"}:
            return "win_amd64"
        if machine in {"x86", "i386", "i686"}:
            return "win32"
        return "win_amd64"

    if sys_platform == "darwin":
        if machine in {"arm64", "aarch64"}:
            return "macosx_11_0_arm64"
        if machine in {"x86_64", "amd64"}:
            return "macosx_11_0_x86_64"
        return "macosx_11_0_x86_64"

    if sys_platform.startswith("linux"):
        if machine in {"x86_64", "amd64"}:
            return "manylinux2014_x86_64"
        if machine in {"aarch64", "arm64"}:
            return "manylinux2014_aarch64"
        return "manylinux2014_x86_64"

    return None


def _internet_probe(allowed: bool) -> dict[str, object]:
    if not allowed:
        return {"attempted": False, "ok": None, "error": "bpy.app.online_access is False"}
    try:
        start = time.time()
        with urllib.request.urlopen("https://pypi.org", timeout=5) as resp:  # noqa: S310
            resp.read(1)
        return {"attempted": True, "ok": True, "error": None, "duration_s": time.time() - start}
    except Exception as exc:
        return {"attempted": True, "ok": False, "error": str(exc)}


python_version_nodot = f"{sys.version_info.major}{sys.version_info.minor}"
platform_tag = _guess_pip_platform_tag()

online_access = getattr(bpy.app, "online_access", None)
online_access_override = getattr(bpy.app, "online_access_override", None)
probe = _internet_probe(bool(online_access)) if online_access is not None else {"attempted": False, "ok": None, "error": "bpy.app.online_access not available"}

python_args = tuple(getattr(bpy.app, "python_args", ()))
python_exe = sys.executable

site_packages: list[dict[str, object]] = []
try:
    for p in site.getsitepackages():
        site_packages.append({"path": p, "writable": _is_writable(p)})
except Exception:
    pass

user_site = None
try:
    user_site = site.getusersitepackages()
except Exception:
    user_site = None

pip_info: dict[str, object] = {"importable": False, "version": None, "command": None}
try:
    import pip  # type: ignore

    pip_info["importable"] = True
    pip_info["version"] = getattr(pip, "__version__", None)
except Exception:
    pass

try:
    import subprocess

    cmd = [python_exe, *python_args, "-m", "pip", "--version"]
    proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    pip_info["command"] = {
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }
except Exception as exc:
    pip_info["command"] = {"error": str(exc)}

data = {
    "blender": {
        "version_string": getattr(bpy.app, "version_string", None),
        "version": getattr(bpy.app, "version", None),
    },
    "python": {
        "version": sys.version,
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
        },
        "platform": sys.platform,
        "machine": platform.machine(),
        "sysconfig_platform": sysconfig.get_platform(),
        "executable": python_exe,
        "python_args": python_args,
        "tempdir": tempfile.gettempdir(),
    },
    "site": {
        "site_packages": site_packages,
        "user_site": user_site,
    },
    "pip": pip_info,
    "network": {
        "online_access": online_access,
        "online_access_override": online_access_override,
        "internet_probe": probe,
    },
    "suggested_pip_download": {
        "python_version": python_version_nodot,
        "platform": platform_tag,
        "implementation": "cp",
        "only_binary": ":all:",
    },
}

print(json.dumps(data, ensure_ascii=True))
"""

    return execute_json(
        code=code,
        port=mcp_port,
        socket_timeout_seconds=30.0,
        remote_timeout_seconds=30.0,
        code_is_base64=True,
    )


def render_remote_python_info(info: dict[str, Any]) -> str:
    """Render `pkg info` JSON into a human-readable report.

    Parameters
    ----------
    info : dict[str, Any]
        JSON object returned by `get_remote_python_info`.

    Returns
    -------
    str
        Multi-line report suitable for console output.
    """
    blender = info.get("blender", {}) if isinstance(info.get("blender"), dict) else {}
    python = info.get("python", {}) if isinstance(info.get("python"), dict) else {}
    pip = info.get("pip", {}) if isinstance(info.get("pip"), dict) else {}
    network = info.get("network", {}) if isinstance(info.get("network"), dict) else {}
    site = info.get("site", {}) if isinstance(info.get("site"), dict) else {}

    lines: list[str] = []
    lines.append("Remote Blender/Python environment:")
    lines.append(f"- Blender: {blender.get('version_string')}")
    lines.append(
        f"- Python: {python.get('version_info', {}).get('major')}.{python.get('version_info', {}).get('minor')}.{python.get('version_info', {}).get('micro')}"
    )
    lines.append(f"- Platform: {python.get('platform')} ({python.get('machine')})")
    lines.append(f"- sys.executable: {python.get('executable')}")
    lines.append(f"- bpy.app.python_args: {python.get('python_args')}")
    lines.append(f"- tempdir: {python.get('tempdir')}")

    site_packages = site.get("site_packages")
    if isinstance(site_packages, list) and site_packages:
        lines.append("- site-packages:")
        for entry in site_packages:
            if not isinstance(entry, dict):
                continue
            lines.append(f"  - {entry.get('path')} (writable={entry.get('writable')})")

    user_site = site.get("user_site")
    if user_site:
        lines.append(f"- user-site: {user_site}")

    pip_command = pip.get("command")
    if isinstance(pip_command, dict):
        if "error" in pip_command:
            lines.append(f"- pip: error checking pip: {pip_command.get('error')}")
        else:
            lines.append(f"- pip: {pip_command.get('stdout') or pip.get('version')}")
            if pip_command.get("stderr"):
                lines.append(f"  stderr: {pip_command.get('stderr')}")
    else:
        lines.append(f"- pip: {pip.get('version') or 'unknown'}")

    online_access = network.get("online_access")
    probe = (
        network.get("internet_probe")
        if isinstance(network.get("internet_probe"), dict)
        else {}
    )
    lines.append(f"- bpy.app.online_access: {online_access}")
    if probe:
        lines.append(
            f"- internet probe: attempted={probe.get('attempted')} ok={probe.get('ok')} error={probe.get('error')}"
        )

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
