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

    def fake_get_remote_python_info(*, port: int | None) -> dict[str, object]:
        assert port == 1234
        return {"ok": True, "port": port}

    monkeypatch.setattr(
        pkg_commands, "get_remote_python_info", fake_get_remote_python_info
    )

    result = CliRunner().invoke(cli, ["pkg", "info", "--port", "1234", "--json"])

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "port": 1234}


def test_pkg_pip_requires_args() -> None:
    from blender_remote.cli import cli

    result = CliRunner().invoke(cli, ["pkg", "pip", "--port", "1"])

    assert result.exit_code != 0
    assert "Usage:" in result.output


def test_install_packages_builds_offline_pip_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from blender_remote.cli.pkg import install as install_module

    captured: dict[str, object] = {}

    def fake_run_pip(*, port: int | None, pip_args: list[str]) -> dict[str, object]:
        captured["port"] = port
        captured["pip_args"] = pip_args
        return {"returncode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(install_module, "run_pip", fake_run_pip)

    install_module.install_packages(
        package_spec=["numpy<2"],
        port=777,
        upgrade=False,
        force_reinstall=False,
        no_deps=False,
        remote_wheelhouse="C:/tmp/wheels",
    )

    assert captured["port"] == 777
    assert captured["pip_args"] == [
        "install",
        "--no-index",
        "--find-links",
        "C:/tmp/wheels",
        "numpy<2",
    ]


def test_install_packages_rejects_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    from blender_remote.cli.pkg import install as install_module

    monkeypatch.setattr(install_module, "run_pip", lambda **_: {"returncode": 0})

    with pytest.raises(ClickException):
        install_module.install_packages(
            package_spec=["git+https://example.com/repo.git"],
            port=1,
            upgrade=False,
            force_reinstall=False,
            no_deps=False,
            remote_wheelhouse=None,
        )


def test_push_wheels_discovers_whl(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from blender_remote.cli.pkg import push as push_module

    (tmp_path / "a.whl").write_bytes(b"wheel-a")
    (tmp_path / "b.whl").write_bytes(b"wheel-b")

    uploaded: list[tuple[Path, str, int]] = []

    def fake_upload_file(
        *, local_path: Path, remote_path: str, port: int, chunk_size: int
    ) -> None:
        uploaded.append((local_path, remote_path, chunk_size))

    monkeypatch.setattr(push_module, "upload_file", fake_upload_file)
    monkeypatch.setattr(push_module, "resolve_mcp_port", lambda _: 6688)

    push_module.push_wheels(
        inputs=[tmp_path],
        remote_wheelhouse="C:\\tmp\\wheels",
        port=None,
        chunk_size=1024,
    )

    remote_paths = sorted(p[1] for p in uploaded)
    assert remote_paths == ["C:/tmp/wheels/a.whl", "C:/tmp/wheels/b.whl"]


def test_upload_file_rejects_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from blender_remote.cli.pkg import upload as upload_module

    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")

    monkeypatch.setattr(upload_module, "execute_json", lambda **_: {})

    with pytest.raises(ClickException):
        upload_module.upload_file(
            local_path=empty,
            remote_path="C:/tmp/empty.bin",
            port=1,
            chunk_size=1024,
        )
