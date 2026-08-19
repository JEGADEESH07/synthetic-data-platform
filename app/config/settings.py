from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class QualityPolicy:
    """
    Defines minimum quality requirements for
    synthetic-data generation.
    """

    minimum_trust_score: float = 0.70

    require_schema_valid: bool = True

    require_privacy_safe: bool = True

    mode: str = "regenerate"

    max_regeneration_attempts: int = 3

@dataclass(frozen=True)
class PipelineConfig:
    """
    Configuration for the V0.2 synthetic-data pipeline.
    """

    default_epochs: int = 300

    default_output_rows: int = 100

    default_output_data_path: str = (
        "data/output/synthetic_data.csv"
    )

    default_output_report_path: str = (
        "data/output/evaluation_report.json"
    )

    max_output_rows: int = 1_000_000

    min_output_rows: int = 1

    min_epochs: int = 1

    max_epochs: int = 10_000

    job_database_path: str = "data/output/jobs.db"


DEFAULT_CONFIG = PipelineConfig()
DEFAULT_QUALITY_POLICY = QualityPolicy()

def validate_quality_policy(
    policy: QualityPolicy,
) -> None:
    """
    Validate quality-policy configuration.
    """

    if not (
        0.0
        <= policy.minimum_trust_score
        <= 1.0
    ):
        raise ValueError(
            "minimum_trust_score must be "
            "between 0.0 and 1.0."
        )

    allowed_modes = {
        "report",
        "block",
        "regenerate",
    }

    if policy.mode not in allowed_modes:
        raise ValueError(
            "mode must be one of: "
            "report, block, regenerate."
        )

    if policy.max_regeneration_attempts < 0:
        raise ValueError(
            "max_regeneration_attempts must "
            "be greater than or equal to zero."
        )

    if (
        policy.mode == "regenerate"
        and policy.max_regeneration_attempts == 0
    ):
        raise ValueError(
            "Regenerate mode requires at least "
            "one regeneration attempt."
        )

def validate_generation_parameters(
    output_rows: int,
    epochs: int,
) -> None:
    """
    Validate generation parameters against platform limits.
    """

    if not (
        DEFAULT_CONFIG.min_output_rows
        <= output_rows
        <= DEFAULT_CONFIG.max_output_rows
    ):
        raise ValueError(
            f"output_rows must be between "
            f"{DEFAULT_CONFIG.min_output_rows} and "
            f"{DEFAULT_CONFIG.max_output_rows}."
        )

    if not (
        DEFAULT_CONFIG.min_epochs
        <= epochs
        <= DEFAULT_CONFIG.max_epochs
    ):
        raise ValueError(
            f"epochs must be between "
            f"{DEFAULT_CONFIG.min_epochs} and "
            f"{DEFAULT_CONFIG.max_epochs}."
        )


def ensure_output_directory(path: str) -> None:
    """
    Ensure the parent directory for an output file exists.
    """

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )