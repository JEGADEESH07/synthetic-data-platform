
"""Configuration snapshot utilities for execution auditing."""

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from synthetic_data.config import PlatformConfig


def _to_snapshot_value(value: Any) -> Any:
    """Convert supported configuration values to JSON-compatible values."""

    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_snapshot_value(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): _to_snapshot_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_to_snapshot_value(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise TypeError(
        f"Unsupported configuration value type: {type(value).__name__}"
    )


def capture_configuration(config: PlatformConfig) -> dict[str, Any]:
    """Return a JSON-compatible snapshot of the effective configuration."""

    if not isinstance(config, PlatformConfig):
        raise TypeError("config must be a PlatformConfig instance.")

    snapshot = _to_snapshot_value(config)

    if not isinstance(snapshot, dict):
        raise TypeError("Configuration snapshot must be a mapping.")

    return snapshot
