"""Tests for the `blender-remote-cli pkg` command group."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click import ClickException
from click.testing import CliRunner


def test_pkg_info_json_outputs_single_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import pkg as pkg_commands

    def fake_get_blender_python_info() -> dict[str, object]:
        return {"ok": True, "python": {"version_info": {"major": 3}}}

    monkeypatch.setattr(
        pkg_commands, "get_blender_python_info", fake_get_blender_python_info
    )

    result = CliRunner().invoke(cli, ["pkg", "info", "--json"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "ok": True,
        "python": {"version_info": {"major": 3}},
    }


def test_pkg_pip_requires_args() -> None:
    from blender_remote.cli import cli

    result = CliRunner().invoke(cli, ["pkg", "pip"])

    assert result.exit_code != 0
    assert "Usage: blender-remote-cli pkg pip -- PIP_ARGS..." in result.output


def test_pkg_pip_forwards_args(monkeypatch: pytest.MonkeyPatch) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import pkg as pkg_commands

    captured: dict[str, object] = {}

    def fake_run_pip(*, pip_args: list[str]) -> None:
        captured["pip_args"] = pip_args

    monkeypatch.setattr(pkg_commands, "run_pip", fake_run_pip)

    result = CliRunner().invoke(
        cli, ["pkg", "pip", "--", "list", "--format=json"], catch_exceptions=False
    )

    assert result.exit_code == 0, result.output
    assert captured["pip_args"] == ["list", "--format=json"]


def test_pkg_bootstrap_forwards_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from blender_remote.cli import cli
    from blender_remote.cli.commands import pkg as pkg_commands

    captured: dict[str, object] = {}

    def fake_bootstrap_pip(
        *, method: str, get_pip_path: Path | None, upgrade: bool
    ) -> None:
        captured["method"] = method
        captured["get_pip_path"] = get_pip_path
        captured["upgrade"] = upgrade

    monkeypatch.setattr(pkg_commands, "bootstrap_pip", fake_bootstrap_pip)

    get_pip = tmp_path / "get-pip.py"
    get_pip.write_text("print('ok')\n", encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        [
            "pkg",
            "bootstrap",
            "--method",
            "get-pip",
            "--get-pip",
            str(get_pip),
            "--upgrade",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert captured["method"] == "get-pip"
    assert captured["get_pip_path"] == get_pip
    assert captured["upgrade"] is True


def test_extract_sentinel_json_extracts_object() -> None:
    from blender_remote.cli.pkg.blender_background import (
        JSON_BEGIN_SENTINEL,
        JSON_END_SENTINEL,
        extract_sentinel_json,
    )

    text = (
        "noise before\n"
        + JSON_BEGIN_SENTINEL
        + "\n"
        + json.dumps({"a": 1})
        + "\n"
        + JSON_END_SENTINEL
        + "\nnoise after\n"
    )

    assert extract_sentinel_json(text) == {"a": 1}


def test_extract_sentinel_json_uses_last_block() -> None:
    from blender_remote.cli.pkg.blender_background import (
        JSON_BEGIN_SENTINEL,
        JSON_END_SENTINEL,
        extract_sentinel_json,
    )

    text = (
        JSON_BEGIN_SENTINEL
        + "\n"
        + json.dumps({"a": 1})
        + "\n"
        + JSON_END_SENTINEL
        + "\n"
        + JSON_BEGIN_SENTINEL
        + "\n"
        + json.dumps({"b": 2})
        + "\n"
        + JSON_END_SENTINEL
        + "\n"
    )

    assert extract_sentinel_json(text) == {"b": 2}


def test_extract_sentinel_json_requires_markers() -> None:
    from blender_remote.cli.pkg.blender_background import extract_sentinel_json

    with pytest.raises(ClickException):
        extract_sentinel_json("no markers here\n")


def test_extract_sentinel_json_value_extracts_array() -> None:
    from blender_remote.cli.pkg.blender_background import (
        JSON_BEGIN_SENTINEL,
        JSON_END_SENTINEL,
        extract_sentinel_json_value,
    )

    text = (
        "noise before\n"
        + JSON_BEGIN_SENTINEL
        + "\n"
        + json.dumps([{"a": 1}, {"b": 2}])
        + "\n"
        + JSON_END_SENTINEL
        + "\nnoise after\n"
    )

    assert extract_sentinel_json_value(text) == [{"a": 1}, {"b": 2}]
