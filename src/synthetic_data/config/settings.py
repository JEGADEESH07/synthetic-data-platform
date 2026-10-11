"""Application configuration."""

from dataclasses import dataclass
from pathlib import Path
from synthetic_data.errors import ConfigurationError
import yaml




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
class PlatformConfig:
    """Complete platform configuration."""

    generation: GenerationConfig
    output: OutputConfig
    quality: QualityConfig
    privacy: PrivacyConfig


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

    _validate_positive_integer(
        generation.default_row_count,
        "generation.default_row_count",
    )

    _validate_positive_integer(
        generation.ctgan_epochs,
        "generation.ctgan_epochs",
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
    )