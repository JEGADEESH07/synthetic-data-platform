"""Dataset profiling."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ColumnProfile:
    """Profile information for one dataset column."""

    name: str
    dtype: str
    row_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int


@dataclass(frozen=True)
class DatasetProfile:
    """Profile information for an entire dataset."""

    row_count: int
    column_count: int
    columns: tuple[ColumnProfile, ...]


def profile_dataset(dataframe: pd.DataFrame) -> DatasetProfile:
    """Create a structural and statistical profile of a dataset."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    if dataframe.empty:
        raise ValueError("Cannot profile an empty dataset")

    row_count = len(dataframe)
    column_profiles: list[ColumnProfile] = []

    for column in dataframe.columns:
        series = dataframe[column]
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        column_profiles.append(
            ColumnProfile(
                name=str(column),
                dtype=str(series.dtype),
                row_count=row_count,
                missing_count=missing_count,
                missing_percentage=(missing_count / row_count) * 100,
                unique_count=unique_count,
            )
        )

    return DatasetProfile(
        row_count=row_count,
        column_count=len(dataframe.columns),
        columns=tuple(column_profiles),
    )
