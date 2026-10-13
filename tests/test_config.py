"""Tests for platform configuration."""

import pytest
from pathlib import Path
from synthetic_data.config import (
    ConfigurationError,
    load_config,
)


def test_load_config_includes_input_settings(tmp_path):
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        """
generation:
  default_row_count: 1000
  ctgan_epochs: 10

output:
  directory: data/output/jobs

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: data/input
  max_file_size_mb: 50
  max_input_rows: 50000
  max_output_rows: 75000
  encoding: utf-8
  allow_symlinks: false
  reject_duplicate_columns: true
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.input.allowed_root == Path("data/input")
    assert config.input.max_file_size_mb == 50
    assert config.input.max_input_rows == 50_000
    assert config.input.max_output_rows == 75_000
    assert config.input.encoding == "utf-8"
    assert config.input.allow_symlinks is False
    assert config.input.reject_duplicate_columns is True


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



@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("default_row_count", 0),
        ("default_row_count", -1),
        ("ctgan_epochs", 0),
        ("ctgan_epochs", -1),
    ],
)
def test_invalid_generation_values_are_rejected(
    tmp_path,
    field,
    value,
):
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(
        f"""
generation:
  default_row_count: 1000
  ctgan_epochs: 10
  {field}: {value}
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_file_size_mb", 0),
        ("max_file_size_mb", -1),
        ("max_input_rows", 0),
        ("max_input_rows", -1),
        ("max_output_rows", 0),
        ("max_output_rows", -1),
    ],
)
def test_invalid_input_limits_are_rejected(
    tmp_path,
    field,
    value,
):
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
generation:
  default_row_count: 1000
  ctgan_epochs: 10

output:
  directory: data/output/jobs

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: data/input
  max_file_size_mb: 100
  max_input_rows: 100000
  max_output_rows: 100000
  encoding: utf-8
  allow_symlinks: false
  reject_duplicate_columns: true
  {field}: {value}
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)


def test_empty_input_allowed_root_is_rejected(tmp_path):
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        """
generation:
  default_row_count: 1000
  ctgan_epochs: 10

output:
  directory: data/output/jobs

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: ""
  max_file_size_mb: 100
  max_input_rows: 100000
  max_output_rows: 100000
  encoding: utf-8
  allow_symlinks: false
  reject_duplicate_columns: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)

def test_empty_input_encoding_is_rejected(tmp_path):
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        """
generation:
  default_row_count: 1000
  ctgan_epochs: 10

output:
  directory: data/output/jobs

quality:
  minimum_score: 0.80

privacy:
  fail_on_exact_match: true

input:
  allowed_root: data/input
  max_file_size_mb: 100
  max_input_rows: 100000
  max_output_rows: 100000
  encoding: ""
  allow_symlinks: false
  reject_duplicate_columns: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)
