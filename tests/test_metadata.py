import pandas as pd
import pytest

from synthetic_data.identifiers import detect_identifiers
from synthetic_data.metadata import (
    ColumnPolicy,
    MetadataPolicy,
    build_metadata_policy,
)


def test_build_metadata_policy() -> None:
    """Metadata policy should classify and protect dataset columns."""

    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002", "C003"],
            "Age": [25, 30, 35],
            "City": ["Chennai", "Madurai", "Chennai"],
            "Amount": [100.0, 250.5, 75.0],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    assert isinstance(policy, MetadataPolicy)
    assert len(policy.columns) == 4

    assert policy.protected_columns == ("Customer_ID",)

    assert policy.trainable_columns == (
        "Age",
        "City",
        "Amount",
    )


def test_column_types() -> None:
    """Metadata should identify generation-relevant column types."""

    dataframe = pd.DataFrame(
        {
            "Age": [20, 30, 40],
            "City": ["Chennai", "Madurai", "Chennai"],
            "Active": [True, False, True],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    columns = {column.name: column for column in policy.columns}

    assert isinstance(columns["Age"], ColumnPolicy)
    assert columns["Age"].column_type == "numerical"
    assert columns["City"].column_type == "categorical"
    assert columns["Active"].column_type == "boolean"


def test_nullable_columns_are_detected() -> None:
    """Metadata should record whether a column contains missing values."""

    dataframe = pd.DataFrame(
        {
            "Age": [20, None, 40],
            "City": ["Chennai", "Madurai", "Chennai"],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    columns = {column.name: column for column in policy.columns}

    assert columns["Age"].nullable is True
    assert columns["City"].nullable is False


def test_empty_dataset_raises_error() -> None:
    """Empty datasets should not produce metadata policies."""

    dataframe = pd.DataFrame()

    detection = detect_identifiers(
        pd.DataFrame({"Customer_ID": ["C001"]})
    )

    with pytest.raises(ValueError, match="empty dataset"):
        build_metadata_policy(dataframe, detection)
