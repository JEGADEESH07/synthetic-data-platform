"""Application configuration."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from synthetic_data.errors import ConfigurationError


@dataclass(frozen=True)
class GenerationConfig:
    """Synthetic generation settings."""

    default_row_count: int = 1000
    ctgan_epochs: int = 10


@dataclass(frozen=True)
class OutputConfig:
    """Output persistence settings."""

    directory: Path = Path("data/output/jobs")


@dataclass(frozen=True)
class QualityConfig:
    """Statistical quality settings."""

    minimum_score: float = 0.80


@dataclass(frozen=True)
class PrivacyConfig:
    """Privacy evaluation settings."""

    fail_on_exact_match: bool = True


@dataclass(frozen=True)
class InputConfig:
    """Input security and ingestion settings."""

    allowed_root: Path = Path("data/input")
    max_file_size_mb: int = 100
    max_input_rows: int = 100_000
    max_output_rows: int = 100_000
    encoding: str = "utf-8"
    allow_symlinks: bool = False
    reject_duplicate_columns: bool = True


@dataclass(frozen=True)
class PlatformConfig:
    """Complete platform configuration."""

    generation: GenerationConfig
    output: OutputConfig
    quality: QualityConfig
    privacy: PrivacyConfig
    input: InputConfig


def _validate_positive_integer(
    value: int,
    name: str,
) -> None:
    """Validate a positive integer configuration value."""

    if not isinstance(value, int):
        raise ConfigurationError(
            f"{name} must be an integer"
        )

    if value <= 0:
        raise ConfigurationError(
            f"{name} must be greater than zero"
        )


def _validate_score(
    value: float,
    name: str,
) -> None:
    """Validate a score between zero and one."""

    if not isinstance(value, (int, float)):
        raise ConfigurationError(
            f"{name} must be numeric"
        )

    if not 0 <= value <= 1:
        raise ConfigurationError(
            f"{name} must be between 0 and 1"
        )


def load_config(
    file_path: str | Path,
) -> PlatformConfig:
    """Load and validate platform configuration from YAML."""

    path = Path(file_path)

    if not path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {path}"
        )

    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ConfigurationError(
            "Configuration file must be YAML"
        )

    try:
        raw = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise ConfigurationError(
            "Could not read configuration file"
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigurationError(
            "Configuration root must be a mapping"
        )

    generation_raw = raw.get(
        "generation",
        {},
    )

    output_raw = raw.get(
        "output",
        {},
    )

    quality_raw = raw.get(
        "quality",
        {},
    )

    privacy_raw = raw.get(
        "privacy",
        {},
    )

    input_raw = raw.get(
        "input",
        {},
    )

    input_allowed_root = input_raw.get(
        "allowed_root",
        "data/input",
    )

    input_encoding = input_raw.get(
        "encoding",
        "utf-8",
    )

    if not str(input_allowed_root).strip():
        raise ConfigurationError(
            "input.allowed_root must not be empty"
        )

    if not str(input_encoding).strip():
        raise ConfigurationError(
            "input.encoding must not be empty"
        )

    generation = GenerationConfig(
        default_row_count=int(
            generation_raw.get(
                "default_row_count",
                1000,
            )
        ),
        ctgan_epochs=int(
            generation_raw.get(
                "ctgan_epochs",
                10,
            )
        ),
    )

    output = OutputConfig(
        directory=Path(
            output_raw.get(
                "directory",
                "data/output/jobs",
            )
        )
    )

    quality = QualityConfig(
        minimum_score=float(
            quality_raw.get(
                "minimum_score",
                0.80,
            )
        )
    )

    privacy = PrivacyConfig(
        fail_on_exact_match=bool(
            privacy_raw.get(
                "fail_on_exact_match",
                True,
            )
        )
    )

    input_config = InputConfig(
        allowed_root=Path(input_allowed_root),
        max_file_size_mb=int(
            input_raw.get(
                "max_file_size_mb",
                100,
            )
        ),
        max_input_rows=int(
            input_raw.get(
                "max_input_rows",
                100_000,
            )
        ),
        max_output_rows=int(
            input_raw.get(
                "max_output_rows",
                100_000,
            )
        ),
        encoding=str(input_encoding),
        allow_symlinks=bool(
            input_raw.get(
                "allow_symlinks",
                False,
            )
        ),
        reject_duplicate_columns=bool(
            input_raw.get(
                "reject_duplicate_columns",
                True,
            )
        ),
    )

    _validate_positive_integer(
        generation.default_row_count,
        "generation.default_row_count",
    )

    _validate_positive_integer(
        generation.ctgan_epochs,
        "generation.ctgan_epochs",
    )

    _validate_positive_integer(
        input_config.max_file_size_mb,
        "input.max_file_size_mb",
    )

    _validate_positive_integer(
        input_config.max_input_rows,
        "input.max_input_rows",
    )

    _validate_positive_integer(
        input_config.max_output_rows,
        "input.max_output_rows",
    )

    _validate_score(
        quality.minimum_score,
        "quality.minimum_score",
    )

    return PlatformConfig(
        generation=generation,
        output=output,
        quality=quality,
        privacy=privacy,
        input=input_config,
    )