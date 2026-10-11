"""CTGAN-based synthetic data generation."""

from dataclasses import dataclass
from synthetic_data.config import GenerationConfig
import pandas as pd
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

from synthetic_data.metadata import MetadataPolicy


class SyntheticGenerationError(Exception):
    """Raised when synthetic data generation fails."""


@dataclass(frozen=True)
class GenerationResult:
    """Result produced by the synthetic data generator."""

    dataframe: pd.DataFrame
    row_count: int


def _build_sdv_metadata(
    dataframe: pd.DataFrame,
    policy: MetadataPolicy,
) -> SingleTableMetadata:
    """Build SDV metadata from our platform policy."""

    metadata = SingleTableMetadata()

    for column in policy.columns:
        # Protected columns must never enter the generator.
        if column.protected:
            continue

        if column.name not in dataframe.columns:
            raise SyntheticGenerationError(
                f"Policy column missing from dataframe: {column.name}"
            )

        if column.column_type == "numerical":
            sdtype = "numerical"
        elif column.column_type == "categorical":
            sdtype = "categorical"
        elif column.column_type == "datetime":
            sdtype = "datetime"
        elif column.column_type == "boolean":
            sdtype = "boolean"
        else:
            sdtype = "categorical"

        metadata.add_column(
            column.name,
            sdtype=sdtype,
        )

    return metadata


def generate_synthetic_data(
    dataframe: pd.DataFrame,
    policy: MetadataPolicy,
    row_count: int,
    config: GenerationConfig | None = None,
) -> GenerationResult:
    """Generate structurally valid synthetic data."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    if row_count <= 0:
        raise ValueError("row_count must be greater than zero")

    generation_config = (
        config
        if config is not None
        else GenerationConfig()
    )
    trainable_columns = list(policy.trainable_columns)

    if not trainable_columns:
        raise SyntheticGenerationError(
            "No trainable columns are available for generation"
        )

    missing_columns = [
        column
        for column in trainable_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise SyntheticGenerationError(
            f"Policy columns missing from dataframe: {missing_columns}"
        )

    training_data = dataframe[trainable_columns].copy()

    if training_data.empty:
        raise SyntheticGenerationError(
            "Training dataset contains no rows"
        )

    try:
        metadata = _build_sdv_metadata(
            training_data,
            policy,
        )

        synthesizer = CTGANSynthesizer(
            metadata,
            epochs=generation_config.ctgan_epochs,
            verbose=False,
        )

        synthesizer.fit(training_data)

        synthetic_data = synthesizer.sample(
            num_rows=row_count
        )

    except Exception as exc:
        raise SyntheticGenerationError(
            "Synthetic data generation failed"
        ) from exc

    expected_columns = set(trainable_columns)
    actual_columns = set(synthetic_data.columns)

    if actual_columns != expected_columns:
        raise SyntheticGenerationError(
            "Generated schema does not match the trainable schema"
        )

    if len(synthetic_data) != row_count:
        raise SyntheticGenerationError(
            "Generator returned an unexpected number of rows"
        )

    return GenerationResult(
        dataframe=synthetic_data[trainable_columns],
        row_count=len(synthetic_data),
    )