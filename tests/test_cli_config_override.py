"""Tests for the blender-remote-cli --config / BLENDER_REMOTE_CONFIG override."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from blender_remote.cli import cli
from blender_remote.cli.config import BlenderRemoteConfig
from blender_remote.cli.constants import CONFIG_FILE


def _write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_config_flag_overrides_default_config_path(tmp_path: Path) -> None:
    custom_config = tmp_path / "custom.yaml"
    _write_config(
        custom_config,
        {
            "blender": {"exec_path": "/not/real/blender"},
            "mcp_service": {"default_port": 7777},
        },
    )

    result = CliRunner().invoke(
        cli,
        ["--config", str(custom_config), "config", "get", "mcp_service.default_port"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "7777" in result.output


def test_config_env_var_overrides_default_config_path(tmp_path: Path) -> None:
    custom_config = tmp_path / "env.yaml"
    _write_config(
        custom_config,
        {
            "blender": {"exec_path": "/not/real/blender"},
            "mcp_service": {"default_port": 8888},
        },
    )

    env = os.environ.copy()
    env["BLENDER_REMOTE_CONFIG"] = str(custom_config)
    result = CliRunner(env=env).invoke(
        cli,
        ["config", "get", "mcp_service.default_port"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "8888" in result.output


def test_config_flag_takes_precedence_over_env_var(tmp_path: Path) -> None:
    env_config = tmp_path / "env.yaml"
    flag_config = tmp_path / "flag.yaml"
    _write_config(env_config, {"mcp_service": {"default_port": 1111}})
    _write_config(flag_config, {"mcp_service": {"default_port": 2222}})

    env = os.environ.copy()
    env["BLENDER_REMOTE_CONFIG"] = str(env_config)
    result = CliRunner(env=env).invoke(
        cli,
        ["--config", str(flag_config), "config", "get", "mcp_service.default_port"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "2222" in result.output
    assert "1111" not in result.output


def test_init_writes_to_custom_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom_config = tmp_path / "nested" / "custom.yaml"
    fake_blender = tmp_path / "fake_blender"
    fake_blender.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_blender.chmod(0o755)

    def fake_detect(blender_path: str | Path) -> dict[str, Any]:
        return {
            "version": "4.4.3",
            "version_tuple": [4, 4, 3],
            "build_date": "2024-01-01",
            "exec_path": str(blender_path),
            "root_dir": str(Path(blender_path).parent),
            "plugin_dir": str(tmp_path / "addons"),
            "user_addons": str(tmp_path / "addons"),
            "all_addon_paths": [str(tmp_path / "addons")],
            "extensions_dir": None,
        }

    monkeypatch.setattr(
        "blender_remote.cli.commands.init.detect_blender_info", fake_detect
    )

    result = CliRunner().invoke(
        cli,
        [
            "--config",
            str(custom_config),
            "init",
            "--backup",
            str(fake_blender),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert custom_config.exists()
    config = BlenderRemoteConfig(config_path=custom_config)
    assert config.get("blender.exec_path") == str(fake_blender)


def test_config_command_propagates_to_nested_group(tmp_path: Path) -> None:
    custom_config = tmp_path / "custom.yaml"
    _write_config(custom_config, {"mcp_service": {"default_port": 3333}})

    result = CliRunner().invoke(
        cli,
        ["--config", str(custom_config), "config", "get", "mcp_service.default_port"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "3333" in result.output


def test_execute_uses_configured_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom_config = tmp_path / "custom.yaml"
    _write_config(custom_config, {"mcp_service": {"default_port": 4444}})

    captured: dict[str, Any] = {}

    def fake_connect(command: str, params: dict[str, Any] | None = None, *, port: int) -> dict[str, Any]:
        captured["port"] = port
        return {"status": "success", "result": {"executed": True, "result": ""}}

    monkeypatch.setattr(
        "blender_remote.cli.commands.execute.connect_and_send_command", fake_connect
    )

    result = CliRunner().invoke(
        cli,
        ["--config", str(custom_config), "execute", "--code", "print(1)"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert captured["port"] == 4444


def test_job_queue_uses_configured_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom_config = tmp_path / "custom.yaml"
    _write_config(custom_config, {"mcp_service": {"default_port": 5555}})

    captured: dict[str, Any] = {}

    def fake_get_queue_status(*, port: int) -> dict[str, Any]:
        captured["port"] = port
        return {"ok": True}

    monkeypatch.setattr(
        "blender_remote.cli.commands.job.transport.get_queue_status", fake_get_queue_status
    )

    result = CliRunner().invoke(
        cli,
        ["--config", str(custom_config), "job", "queue"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert captured["port"] == 5555


def test_addon_info_uses_configured_blender(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom_config = tmp_path / "custom.yaml"
    fake_blender = tmp_path / "fake_blender"
    fake_blender.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_blender.chmod(0o755)
    _write_config(
        custom_config,
        {
            "blender": {"exec_path": str(fake_blender)},
            "cli": {"timeout_sec": 30},
        },
    )

    captured: dict[str, Any] = {}

    def fake_run_json(*, blender_executable: Path, python_script: str, timeout_seconds: float, factory_startup: bool) -> dict[str, Any]:
        captured["blender_executable"] = blender_executable
        captured["timeout_seconds"] = timeout_seconds
        return {"name": "some_addon", "enabled": True, "loaded": True}

    monkeypatch.setattr(
        "blender_remote.cli.commands.addon.run_blender_background_json", fake_run_json
    )

    result = CliRunner().invoke(
        cli,
        ["--config", str(custom_config), "addon", "info", "some_addon"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert captured["blender_executable"] == fake_blender
    assert captured["timeout_seconds"] == 30


def test_mcp_server_honors_blender_remote_config_env_var(
    tmp_path: Path,
) -> None:
    custom_config = tmp_path / "mcp.yaml"
    _write_config(custom_config, {"mcp_service": {"default_port": 6666}})

    script = f"""
import os
os.environ["BLENDER_REMOTE_CONFIG"] = {str(custom_config)!r}
from blender_remote.mcp_server import get_default_blender_port
print(get_default_blender_port())
"""
    result = __import__("subprocess").run(
        [__import__("sys").executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "6666" in result.stdout


def test_default_config_path_when_no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLENDER_REMOTE_CONFIG", raising=False)
    config = BlenderRemoteConfig()
    assert config.config_path == CONFIG_FILE
