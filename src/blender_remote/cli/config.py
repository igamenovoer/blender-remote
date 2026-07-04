"""Configuration management for the blender-remote CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import click
from omegaconf import DictConfig, OmegaConf

from .constants import CONFIG_FILE, DEFAULT_CLI_TIMEOUT_SECONDS

_DEFAULT_CONFIG: dict[str, Any] = {"cli": {"timeout_sec": DEFAULT_CLI_TIMEOUT_SECONDS}}


class BlenderRemoteConfig:
    """OmegaConf-based configuration manager for blender-remote."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path is not None else CONFIG_FILE
        self.config: DictConfig | None = None

    def load(self) -> DictConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise click.ClickException(
                f"Configuration file not found: {self.config_path}\nRun 'blender-remote-cli init [blender_path]' first"
            )

        loaded = OmegaConf.load(self.config_path)
        merged = OmegaConf.merge(OmegaConf.create(_DEFAULT_CONFIG), loaded)
        # We expect the root of the config to be a mapping (DictConfig)
        self.config = cast(DictConfig, merged)
        return self.config

    def save(self, config: dict[str, Any] | DictConfig) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert dict to DictConfig if needed
        if isinstance(config, dict):
            config = OmegaConf.create(config)

        # Save to file
        OmegaConf.save(config, self.config_path)
        self.config = config

    def get(self, key: str) -> Any:
        """Get configuration value using dot notation."""
        if self.config is None:
            self.load()
        assert self.config is not None

        # Use OmegaConf.select for safe access with None default
        return OmegaConf.select(self.config, key)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        if self.config is None:
            self.load()
        assert self.config is not None

        # Use OmegaConf.update for dot notation setting
        OmegaConf.update(self.config, key, value, merge=True)

        # Save the updated configuration
        OmegaConf.save(self.config, self.config_path)


def current_config() -> BlenderRemoteConfig:
    """Return a :class:`BlenderRemoteConfig` using the CLI context path if available.

    This helper lets commands and helpers pick up the effective config path
    resolved from the global ``--config`` option (or ``BLENDER_REMOTE_CONFIG``)
    without threading ``click.Context`` through every call site.
    """
    try:
        ctx = click.get_current_context()
        config_path = ctx.obj.get("config_path") if ctx.obj else None
    except RuntimeError:
        config_path = None
    return BlenderRemoteConfig(config_path=config_path)
