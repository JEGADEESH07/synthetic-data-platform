from dataclasses import dataclass
from pathlib import Path


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


DEFAULT_CONFIG = PipelineConfig()


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