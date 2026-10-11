import pandas as pd
import pytest

from synthetic_data.generation import (
    GenerationResult,
    SyntheticGenerationError,
    generate_synthetic_data,
)
from synthetic_data.identifiers import detect_identifiers
from synthetic_data.metadata import build_metadata_policy


def test_generate_synthetic_data() -> None:
    """The generator should produce the requested number of rows."""

    dataframe = pd.DataFrame(
        {
            "Customer_ID": [f"C{i:03d}" for i in range(30)],
            "Age": list(range(20, 50)),
            "City": [
                "Chennai",
                "Madurai",
                "Coimbatore",
                "Chennai",
                "Trichy",
            ]
            * 6,
            "Amount": [100.0 + i * 25 for i in range(30)],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    result = generate_synthetic_data(
        dataframe=dataframe,
        policy=policy,
        row_count=20,
    )

    assert isinstance(result, GenerationResult)
    assert result.row_count == 20
    assert len(result.dataframe) == 20

    assert "Age" in result.dataframe.columns
    assert "City" in result.dataframe.columns
    assert "Amount" in result.dataframe.columns

    # Protected identifiers must never enter the generator.
    assert "Customer_ID" not in result.dataframe.columns


def test_invalid_row_count_raises_error() -> None:
    """A non-positive row count should be rejected."""

    dataframe = pd.DataFrame(
        {
            "Age": [20, 30],
            "City": ["Chennai", "Madurai"],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    with pytest.raises(ValueError, match="greater than zero"):
        generate_synthetic_data(
            dataframe=dataframe,
            policy=policy,
            row_count=0,
        )


def test_no_trainable_columns_raises_error() -> None:
    """Generation should fail when every column is protected."""

    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Email": ["a@example.com", "b@example.com"],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    with pytest.raises(
        SyntheticGenerationError,
        match="No trainable columns",
    ):
        generate_synthetic_data(
            dataframe=dataframe,
            policy=policy,
            row_count=10,
        )

def test_invalid_dataframe_type_raises_error() -> None:
    """Generation should reject non-DataFrame input."""

    dataframe = pd.DataFrame(
        {
            "Age": [20, 30],
            "City": ["Chennai", "Madurai"],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    with pytest.raises(
        TypeError,
        match="dataframe must be a pandas DataFrame",
    ):
        generate_synthetic_data(
            dataframe="not a dataframe",
            policy=policy,
            row_count=10,
        )


def test_missing_policy_column_raises_error() -> None:
    """Generation should reject a policy that references a missing column."""

    dataframe = pd.DataFrame(
        {
            "Age": [20, 30],
            "City": ["Chennai", "Madurai"],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    # Remove one trainable column from the actual input.
    dataframe = dataframe[["Age"]]

    with pytest.raises(
        SyntheticGenerationError,
        match="Policy columns missing from dataframe",
    ):
        generate_synthetic_data(
            dataframe=dataframe,
            policy=policy,
            row_count=10,
        )