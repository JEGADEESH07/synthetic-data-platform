"""Synthetic dataset schema validation."""

from dataclasses import dataclass

import pandas as pd


class SchemaValidationError(Exception):
    """Raised when synthetic data fails schema validation."""


@dataclass(frozen=True)
class SchemaValidationResult:
    """Result of schema validation."""

    valid: bool
    row_count: int
    column_count: int
    columns: tuple[str, ...]


def validate_schema(
    source_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
) -> SchemaValidationResult:
    """Validate the structural schema of synthetic data."""

    if not isinstance(source_dataframe, pd.DataFrame):
        raise TypeError(
            "source_dataframe must be a pandas DataFrame"
        )

    if not isinstance(synthetic_dataframe, pd.DataFrame):
        raise TypeError(
            "synthetic_dataframe must be a pandas DataFrame"
        )

    source_columns = list(source_dataframe.columns)
    synthetic_columns = list(synthetic_dataframe.columns)

    if source_columns != synthetic_columns:
        raise SchemaValidationError(
            "Synthetic column structure does not match "
            "the source schema"
        )

    if len(synthetic_dataframe) == 0:
        raise SchemaValidationError(
            "Synthetic dataset contains no rows"
        )

    if len(synthetic_dataframe.columns) == 0:
        raise SchemaValidationError(
            "Synthetic dataset contains no columns"
        )

    return SchemaValidationResult(
        valid=True,
        row_count=len(synthetic_dataframe),
        column_count=len(synthetic_dataframe.columns),
        columns=tuple(synthetic_dataframe.columns),
    )