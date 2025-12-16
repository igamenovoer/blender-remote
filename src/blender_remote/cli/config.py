"""Configuration management for the blender-remote CLI."""

from __future__ import annotations

from typing import Any, cast

import click
from omegaconf import DictConfig, OmegaConf

from .constants import CONFIG_DIR, CONFIG_FILE


class BlenderRemoteConfig:
    """OmegaConf-based configuration manager for blender-remote."""

    def __init__(self) -> None:
        self.config_path = CONFIG_FILE
        self.config: DictConfig | None = None

    def load(self) -> DictConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise click.ClickException(
                f"Configuration file not found: {self.config_path}\nRun 'blender-remote-cli init [blender_path]' first"
            )

        loaded = OmegaConf.load(self.config_path)
        # We expect the root of the config to be a mapping (DictConfig)
        self.config = cast(DictConfig, loaded)
        return self.config

    def save(self, config: dict[str, Any] | DictConfig) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

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

