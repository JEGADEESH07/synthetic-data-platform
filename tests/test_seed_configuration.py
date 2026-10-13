
from dataclasses import replace

import pytest
from synthetic_data.config import GenerationConfig, load_config
from synthetic_data.errors import ConfigurationError


def test_generation_config_has_default_seed():
    config = GenerationConfig()

    assert config.seed == 42


def test_loaded_config_contains_seed():
    config = load_config("config/default.yaml")

    assert config.generation.seed == 42


def test_generation_config_accepts_zero_seed(tmp_path):
    config_path = tmp_path / "seed_zero.yaml"
    config_path.write_text(
        """
generation:
  default_row_count: 1000
  ctgan_epochs: 10
  seed: 0
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
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.generation.seed == 0



@pytest.mark.parametrize("invalid_seed", [-1, True])
def test_generation_config_rejects_invalid_seed(
    tmp_path,
    invalid_seed,
):
    config_path = tmp_path / "invalid_seed.yaml"
    config_path.write_text(
        f"""
generation:
  default_row_count: 1000
  ctgan_epochs: 10
  seed: {str(invalid_seed).lower() if isinstance(invalid_seed, bool) else invalid_seed}
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
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_path)



def test_seed_can_be_changed_without_mutating_original():
    original = GenerationConfig()
    updated = replace(original, seed=123)

    assert original.seed == 42
    assert updated.seed == 123
