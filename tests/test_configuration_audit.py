
import json
from pathlib import Path

import pytest

from synthetic_data.audit.configuration import capture_configuration
from synthetic_data.config import load_config


def test_configuration_snapshot_contains_all_sections():
    config = load_config("config/default.yaml")

    snapshot = capture_configuration(config)

    assert set(snapshot) == {
        "generation",
        "output",
        "quality",
        "privacy",
        "input",
    }


def test_configuration_snapshot_contains_effective_values():
    config = load_config("config/default.yaml")

    snapshot = capture_configuration(config)

    assert snapshot["generation"]["default_row_count"] == 1000
    assert snapshot["generation"]["ctgan_epochs"] == 10
    assert snapshot["quality"]["minimum_score"] == 0.80
    assert snapshot["privacy"]["fail_on_exact_match"] is True


def test_configuration_snapshot_converts_paths_to_strings():
    config = load_config("config/default.yaml")

    snapshot = capture_configuration(config)

    assert isinstance(snapshot["output"]["directory"], str)
    assert isinstance(snapshot["input"]["allowed_root"], str)


def test_configuration_snapshot_is_json_serializable():
    config = load_config("config/default.yaml")

    snapshot = capture_configuration(config)

    restored = json.loads(json.dumps(snapshot))

    assert restored == snapshot


def test_configuration_snapshot_rejects_wrong_input():
    with pytest.raises(TypeError, match="PlatformConfig"):
        capture_configuration({"generation": {}})


def test_snapshot_reflects_the_supplied_configuration(tmp_path):
    config_path = tmp_path / "custom.yaml"
    config_path.write_text(
        """
generation:
  default_row_count: 250
  ctgan_epochs: 5
output:
  directory: custom-output
quality:
  minimum_score: 0.75
privacy:
  fail_on_exact_match: true
input:
  allowed_root: custom-input
  max_file_size_mb: 20
  max_input_rows: 5000
  max_output_rows: 8000
  encoding: utf-8
  allow_symlinks: false
  reject_duplicate_columns: true
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    snapshot = capture_configuration(config)

    assert snapshot["generation"]["default_row_count"] == 250
    assert snapshot["generation"]["ctgan_epochs"] == 5
    assert snapshot["output"]["directory"] == str(Path("custom-output"))
    assert snapshot["quality"]["minimum_score"] == 0.75
    assert snapshot["input"]["max_file_size_mb"] == 20
