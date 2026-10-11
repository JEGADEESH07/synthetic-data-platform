import pandas as pd
import pytest

from synthetic_data.profiling import (
    ColumnProfile,
    DatasetProfile,
    profile_dataset,
)


def test_profile_dataset() -> None:
    """Dataset profiling should return correct structural information."""
    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002", "C003"],
            "Age": [25, 30, 35],
            "City": ["Chennai", "Madurai", None],
        }
    )

    profile = profile_dataset(dataframe)

    assert isinstance(profile, DatasetProfile)
    assert profile.row_count == 3
    assert profile.column_count == 3
    assert len(profile.columns) == 3


def test_column_profile_values() -> None:
    """Column profiles should contain correct statistics."""
    dataframe = pd.DataFrame(
        {
            "Age": [25, 30, None, 30],
        }
    )

    profile = profile_dataset(dataframe)

    column = profile.columns[0]

    assert isinstance(column, ColumnProfile)
    assert column.name == "Age"
    assert column.row_count == 4
    assert column.missing_count == 1
    assert column.missing_percentage == 25.0
    assert column.unique_count == 2


def test_profile_preserves_column_order() -> None:
    """Column profiles should preserve the original dataset order."""
    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001"],
            "Amount": [100],
            "City": ["Chennai"],
        }
    )

    profile = profile_dataset(dataframe)

    assert [column.name for column in profile.columns] == [
        "Customer_ID",
        "Amount",
        "City",
    ]


def test_empty_dataset_raises_error() -> None:
    """Empty datasets should not be profiled."""
    dataframe = pd.DataFrame()

    with pytest.raises(ValueError, match="empty dataset"):
        profile_dataset(dataframe)


def test_invalid_input_raises_error() -> None:
    """Non-DataFrame input should be rejected."""
    with pytest.raises(TypeError, match="pandas DataFrame"):
        profile_dataset({"Age": [25, 30]})
