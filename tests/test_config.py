"""Tests for platform configuration."""

import pytest
from pathlib import Path
from synthetic_data.config import (
    ConfigurationError,
    load_config,
)


def test_load_config():
    """Valid YAML should produce a platform configuration."""

    config = load_config(
        "config/default.yaml"
    )

    assert config.generation.default_row_count == 1000

    assert config.generation.ctgan_epochs == 10

    assert config.output.directory == Path(
        "data/output/jobs"
    )

    assert config.quality.minimum_score == 0.80

    assert config.privacy.fail_on_exact_match is True


def test_missing_config_file_is_rejected(
    tmp_path,
):
    """Missing configuration should fail clearly."""

    with pytest.raises(ConfigurationError):
        load_config(
            tmp_path / "missing.yaml"
        )


def test_non_yaml_config_is_rejected(
    tmp_path,
):
    """Non-YAML files should be rejected."""

    config_file = tmp_path / "config.txt"

    config_file.write_text(
        "hello",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)


def test_invalid_quality_score_is_rejected(
    tmp_path,
):
    """Quality threshold must be between zero and one."""

    config_file = tmp_path / "invalid.yaml"

    config_file.write_text(
        """
generation:
  default_row_count: 1000
  ctgan_epochs: 10

quality:
  minimum_score: 1.5
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)


def test_invalid_generation_values_are_rejected(
    tmp_path,
):
    """Generation values must be positive."""

    config_file = tmp_path / "invalid.yaml"

    config_file.write_text(
        """
generation:
  default_row_count: 0
  ctgan_epochs: 10
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)