"""Convenience wrapper for remote pip installs.

The `pkg install` command intentionally supports only simple package specs
(name/version constraints). For advanced pip usage (URLs, VCS, local paths,
markers, etc.), use `pkg pip -- ...`.
"""

from __future__ import annotations

import re

import click

from blender_remote.cli.pkg.pip import run_pip

_DISALLOWED_SPEC_PREFIXES = ("-",)


def _validate_simple_package_specs(package_spec: list[str]) -> None:
    """Validate that package specs are safe/simple for the `pkg install` wrapper.

    Parameters
    ----------
    package_spec : list[str]
        One or more package requirement specifiers.

    Raises
    ------
    click.ClickException
        If any spec appears to require advanced pip behavior (URLs, VCS, local
        paths, environment markers, or flags).
    """
    for spec in package_spec:
        if not spec or spec.isspace():
            raise click.ClickException("Package spec cannot be empty")

        if spec.startswith(_DISALLOWED_SPEC_PREFIXES):
            raise click.ClickException(
                f"Unsupported package spec '{spec}'. Use 'pkg pip -- ...' for advanced pip usage."
            )

        if "://" in spec or spec.startswith(("git+", "hg+", "svn+", "bzr+")):
            raise click.ClickException(
                f"Unsupported package spec '{spec}'. Use 'pkg pip -- ...' for VCS/URL installs."
            )

        if "@" in spec:
            raise click.ClickException(
                f"Unsupported package spec '{spec}'. Use 'pkg pip -- ...' for direct references."
            )

        if "/" in spec or "\\" in spec:
            raise click.ClickException(
                f"Unsupported package spec '{spec}'. Use 'pkg pip -- ...' for local paths."
            )

        if ";" in spec:
            raise click.ClickException(
                f"Unsupported package spec '{spec}'. Use 'pkg pip -- ...' for environment markers."
            )

        if re.search(r"\s", spec):
            raise click.ClickException(f"Package spec contains whitespace: '{spec}'")


def install_packages(
    *,
    package_spec: list[str],
    port: int | None,
    upgrade: bool,
    force_reinstall: bool,
    no_deps: bool,
    remote_wheelhouse: str | None,
) -> None:
    """Install packages into the remote Blender Python environment.

    Parameters
    ----------
    package_spec : list[str]
        One or more simple package specs (e.g. `["joblib==1.5.3"]`).
    port : int, optional
        Optional MCP port override.
    upgrade : bool
        If True, pass `--upgrade` to pip.
    force_reinstall : bool
        If True, pass `--force-reinstall` to pip.
    no_deps : bool
        If True, pass `--no-deps` to pip.
    remote_wheelhouse : str, optional
        Remote wheelhouse directory. When provided, installs are offline and
        pip is invoked with `--no-index --find-links <DIR>`.

    Raises
    ------
    click.ClickException
        If package specs are invalid or the remote pip invocation fails.
    """
    if not package_spec:
        raise click.ClickException("Must provide one or more PACKAGE_SPEC values")

    _validate_simple_package_specs(package_spec)

    pip_args: list[str] = ["install"]

    if upgrade:
        pip_args.append("--upgrade")
    if force_reinstall:
        pip_args.append("--force-reinstall")
    if no_deps:
        pip_args.append("--no-deps")

    if remote_wheelhouse is not None:
        pip_args.extend(["--no-index", "--find-links", remote_wheelhouse])

    pip_args.extend(package_spec)

    run_pip(port=port, pip_args=pip_args)
