"""Metadata policy generation."""

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from synthetic_data.identifiers import IdentifierDetection


ColumnType = Literal["numerical", "categorical", "datetime", "boolean", "text"]


@dataclass(frozen=True)
class ColumnPolicy:
    """Generation policy for one dataset column."""

    name: str
    column_type: ColumnType
    protected: bool
    nullable: bool
    unique_count: int


@dataclass(frozen=True)
class MetadataPolicy:
    """Generation policy for an entire dataset."""

    columns: tuple[ColumnPolicy, ...]

    @property
    def trainable_columns(self) -> tuple[str, ...]:
        """Return columns permitted for synthetic-data generation."""
        return tuple(
            column.name
            for column in self.columns
            if not column.protected
        )

    @property
    def protected_columns(self) -> tuple[str, ...]:
        """Return columns excluded from synthetic-data generation."""
        return tuple(
            column.name
            for column in self.columns
            if column.protected
        )


def _infer_column_type(series: pd.Series) -> ColumnType:
    """Infer the generation-oriented type of a column."""

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        return "numerical"

    if pd.api.types.is_object_dtype(series):
        return "categorical"

    return "text"


def build_metadata_policy(
    dataframe: pd.DataFrame,
    detection: IdentifierDetection,
) -> MetadataPolicy:
    """Build an explicit generation policy from a dataset."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    if dataframe.empty:
        raise ValueError("Cannot build metadata policy for an empty dataset")

    protected = set(detection.protected_columns)
    policies: list[ColumnPolicy] = []

    for column in dataframe.columns:
        series = dataframe[column]

        policies.append(
            ColumnPolicy(
                name=str(column),
                column_type=_infer_column_type(series),
                protected=str(column) in protected,
                nullable=bool(series.isna().any()),
                unique_count=int(series.nunique(dropna=True)),
            )
        )

    return MetadataPolicy(columns=tuple(policies))
