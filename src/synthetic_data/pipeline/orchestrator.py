"""End-to-end synthetic data pipeline orchestration."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from synthetic_data.config import (
    PlatformConfig,
    load_config,
)
from synthetic_data.generation import (
    GenerationResult,
    generate_synthetic_data,
)
from synthetic_data.identifiers import (
    IdentifierDetection,
    IdentifierGenerationResult,
    detect_identifiers,
    generate_fresh_identifiers,
)
from synthetic_data.ingestion import load_csv
from synthetic_data.logging_config import get_logger
from synthetic_data.metadata import (
    MetadataPolicy,
    build_metadata_policy,
)
from synthetic_data.profiling import (
    DatasetProfile,
    profile_dataset,
)


logger = get_logger("pipeline")


@dataclass(frozen=True)
class PipelineResult:
    """Complete result produced by the V0.2 pipeline."""

    source_dataframe: pd.DataFrame
    profile: DatasetProfile
    detection: IdentifierDetection
    policy: MetadataPolicy
    generation: GenerationResult
    identifiers: IdentifierGenerationResult

    @property
    def synthetic_dataframe(self) -> pd.DataFrame:
        """Return the complete synthetic dataset."""

        return self.identifiers.dataframe


def run_pipeline(
    file_path: str | Path,
    row_count: int | None = None,
    config: PlatformConfig | None = None,
) -> PipelineResult:
    """Run the complete V0.2 synthetic-data generation flow."""

    active_config = config or load_config("config/default.yaml")    
    
    resolved_row_count = (
        row_count
        if row_count is not None
        else active_config.generation.default_row_count
    )

    logger.info(
        "Pipeline started | requested_rows=%s",
        resolved_row_count,
    )

    source_dataframe = load_csv(
        file_path,
        config=active_config.input,
    )

    logger.info(
        "Dataset loaded | rows=%d | columns=%d",
        len(source_dataframe),
        len(source_dataframe.columns),
    )

    profile = profile_dataset(source_dataframe)

    logger.info(
        "Dataset profiling completed | rows=%d | columns=%d",
        profile.row_count,
        profile.column_count,
    )

    detection = detect_identifiers(source_dataframe)

    logger.info(
        "Identifier detection completed | protected_columns=%d",
        len(detection.direct_identifiers),
    )

    policy = build_metadata_policy(
        source_dataframe,
        detection,
    )

    logger.info(
        "Metadata policy created | trainable_columns=%d",
        len(policy.trainable_columns),
    )

    generation = generate_synthetic_data(
        dataframe=source_dataframe,
        policy=policy,
        row_count=resolved_row_count,
        config=active_config.generation,
    )

    logger.info(
        "Synthetic generation completed | rows=%d",
        generation.row_count,
    )

    identifiers = generate_fresh_identifiers(
        original_dataframe=source_dataframe,
        synthetic_dataframe=generation.dataframe,
        detection=detection,
    )

    logger.info(
        "Fresh identifier generation completed | generated_columns=%d",
        len(identifiers.generated_columns),
    )

    logger.info(
        "Pipeline completed successfully | synthetic_rows=%d",
        len(identifiers.dataframe),
    )

    return PipelineResult(
        source_dataframe=source_dataframe,
        profile=profile,
        detection=detection,
        policy=policy,
        generation=generation,
        identifiers=identifiers,
    )