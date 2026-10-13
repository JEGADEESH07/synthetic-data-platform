import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from synthetic_data.config import GenerationConfig
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


def test_same_seed_repeats_actual_synthetic_generation():
    """Check whether independent CTGAN runs repeat with the same seed."""
    dataframe = pd.DataFrame(
        {
            "Age": list(range(20, 40)),
            "City": ["Chennai", "Madurai", "Trichy", "Salem"] * 5,
            "Amount": [100.0 + index * 10 for index in range(20)],
        }
    )

    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    config = GenerationConfig(
        default_row_count=10,
        ctgan_epochs=2,
        seed=42,
    )

    first = generate_synthetic_data(
        dataframe=dataframe,
        policy=policy,
        row_count=10,
        config=config,
    )

    second = generate_synthetic_data(
        dataframe=dataframe,
        policy=policy,
        row_count=10,
        config=config,
    )

    assert_frame_equal(
        first.dataframe.reset_index(drop=True),
        second.dataframe.reset_index(drop=True),
        check_exact=True,
    )


@pytest.mark.parametrize(
    ("dataframe", "expected_columns"),
    [
        pytest.param(
            pd.DataFrame(
                {
                    "Age": [20, 25, 30, 35, 40, 45],
                    "Income": [20000, 25000, 30000, 35000, 40000, 45000],
                }
            ),
            {"Age", "Income"},
            id="numerical-only",
        ),
        pytest.param(
            pd.DataFrame(
                {
                    "City": [
                        "Chennai",
                        "Madurai",
                        "Salem",
                        "Trichy",
                        "Chennai",
                        "Madurai",
                    ],
                    "Department": [
                        "Sales",
                        "Engineering",
                        "HR",
                        "Sales",
                        "Engineering",
                        "HR",
                    ],
                }
            ),
            {"City", "Department"},
            id="categorical-only",
        ),
        pytest.param(
            pd.DataFrame(
                {
                    "Age": [20, 25, 30, 35, 40, 45],
                    "City": [
                        "Chennai",
                        "Madurai",
                        "Salem",
                        "Trichy",
                        "Chennai",
                        "Madurai",
                    ],
                    "Active": [True, False, True, False, True, False],
                }
            ),
            {"Age", "City", "Active"},
            id="mixed-with-boolean",
        ),
    ],
)
def test_generation_supports_diverse_dataset_shapes(
    dataframe: pd.DataFrame,
    expected_columns: set[str],
) -> None:
    """Generation should handle supported numerical and categorical shapes."""
    detection = detect_identifiers(dataframe)
    policy = build_metadata_policy(dataframe, detection)

    config = GenerationConfig(
        default_row_count=5,
        ctgan_epochs=2,
        seed=42,
    )

    result = generate_synthetic_data(
        dataframe=dataframe,
        policy=policy,
        row_count=5,
        config=config,
    )

    assert result.row_count == 5
    assert len(result.dataframe) == 5
    assert set(result.dataframe.columns) == expected_columns
