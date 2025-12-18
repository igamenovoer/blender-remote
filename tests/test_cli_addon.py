"""Tests for the `blender-remote-cli addon` command group."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner


def test_addon_list_json_outputs_single_json_array(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import addon as addon_commands

    def fake_get_configured_blender_executable() -> Path:
        return Path("blender")

    def fake_get_cli_timeout_seconds(*, default: float = 300.0) -> float:
        return 1.0

    def fake_run_blender_background_json_value(
        *,
        blender_executable: Path,
        python_script: str,
        timeout_seconds: float,
        factory_startup: bool = True,
    ) -> list[dict[str, object]]:
        return [
            {"name": "b", "enabled": False, "source": "user"},
            {"name": "a", "enabled": True, "source": "user"},
        ]

    monkeypatch.setattr(
        addon_commands,
        "get_configured_blender_executable",
        fake_get_configured_blender_executable,
    )
    monkeypatch.setattr(
        addon_commands, "get_cli_timeout_seconds", fake_get_cli_timeout_seconds
    )
    monkeypatch.setattr(
        addon_commands,
        "run_blender_background_json_value",
        fake_run_blender_background_json_value,
    )

    result = CliRunner().invoke(cli, ["addon", "list", "--json"])

    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    assert json.loads(result.stdout) == [
        {"name": "a", "enabled": True, "source": "user"},
        {"name": "b", "enabled": False, "source": "user"},
    ]


def test_addon_info_json_not_found_outputs_empty_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import addon as addon_commands

    def fake_get_configured_blender_executable() -> Path:
        return Path("blender")

    def fake_get_cli_timeout_seconds(*, default: float = 300.0) -> float:
        return 1.0

    def fake_run_blender_background_json(
        *,
        blender_executable: Path,
        python_script: str,
        timeout_seconds: float,
        factory_startup: bool = True,
    ) -> dict[str, object]:
        return {}

    monkeypatch.setattr(
        addon_commands,
        "get_configured_blender_executable",
        fake_get_configured_blender_executable,
    )
    monkeypatch.setattr(
        addon_commands, "get_cli_timeout_seconds", fake_get_cli_timeout_seconds
    )
    monkeypatch.setattr(
        addon_commands,
        "run_blender_background_json",
        fake_run_blender_background_json,
    )

    result = CliRunner().invoke(cli, ["addon", "info", "missing", "--json"])

    assert result.exit_code != 0
    assert json.loads(result.stdout) == {}
    assert "Add-on not found" in result.stderr


def test_addon_uninstall_refuses_outside_user_addons_without_force(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import addon as addon_commands

    user_addons = tmp_path / "user_addons"
    user_addons.mkdir()

    external_root = tmp_path / "external"
    external_root.mkdir()
    addon_dir = external_root / "example_addon"
    addon_dir.mkdir()
    addon_init = addon_dir / "__init__.py"
    addon_init.write_text("x = 1\n", encoding="utf-8")

    def fake_get_configured_blender_executable() -> Path:
        return Path("blender")

    def fake_get_cli_timeout_seconds(*, default: float = 300.0) -> float:
        return 1.0

    calls: dict[str, int] = {"count": 0}

    def fake_run_blender_background_json(
        *,
        blender_executable: Path,
        python_script: str,
        timeout_seconds: float,
        factory_startup: bool = True,
    ) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "found": True,
                "module_name": "example_addon",
                "enabled": True,
                "loaded": True,
                "file_path": str(addon_init),
                "user_addons": str(user_addons),
            }
        raise AssertionError("Uninstall should refuse before disabling the add-on")

    monkeypatch.setattr(
        addon_commands,
        "get_configured_blender_executable",
        fake_get_configured_blender_executable,
    )
    monkeypatch.setattr(
        addon_commands, "get_cli_timeout_seconds", fake_get_cli_timeout_seconds
    )
    monkeypatch.setattr(
        addon_commands,
        "run_blender_background_json",
        fake_run_blender_background_json,
    )

    result = CliRunner().invoke(cli, ["addon", "uninstall", "example_addon", "--json"])

    assert result.exit_code != 0
    assert calls["count"] == 1
    assert addon_init.exists()
    assert json.loads(result.stdout)["removed"] is False
    assert "--force" in result.stderr


def test_addon_uninstall_removes_user_addon_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import addon as addon_commands

    user_addons = tmp_path / "user_addons"
    user_addons.mkdir()

    addon_dir = user_addons / "example_addon"
    addon_dir.mkdir()
    addon_init = addon_dir / "__init__.py"
    addon_init.write_text("x = 1\n", encoding="utf-8")

    def fake_get_configured_blender_executable() -> Path:
        return Path("blender")

    def fake_get_cli_timeout_seconds(*, default: float = 300.0) -> float:
        return 1.0

    calls: dict[str, int] = {"count": 0}

    def fake_run_blender_background_json(
        *,
        blender_executable: Path,
        python_script: str,
        timeout_seconds: float,
        factory_startup: bool = True,
    ) -> dict[str, object]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "found": True,
                "module_name": "example_addon",
                "enabled": True,
                "loaded": True,
                "file_path": str(addon_init),
                "user_addons": str(user_addons),
            }
        return {
            "op": "disable",
            "module_name": "example_addon",
            "enabled": False,
            "loaded": False,
        }

    monkeypatch.setattr(
        addon_commands,
        "get_configured_blender_executable",
        fake_get_configured_blender_executable,
    )
    monkeypatch.setattr(
        addon_commands, "get_cli_timeout_seconds", fake_get_cli_timeout_seconds
    )
    monkeypatch.setattr(
        addon_commands,
        "run_blender_background_json",
        fake_run_blender_background_json,
    )

    result = CliRunner().invoke(cli, ["addon", "uninstall", "example_addon", "--json"])

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["removed"] is True
    assert parsed["removed_path"] is not None
    assert not addon_dir.exists()
    assert calls["count"] == 2
