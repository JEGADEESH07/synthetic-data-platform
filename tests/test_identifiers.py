import pandas as pd
import pytest

from synthetic_data.identifiers import (
    IdentifierDetection,
    detect_identifiers,
    generate_fresh_identifiers,
    remove_identifiers,
)


def test_detect_direct_identifiers() -> None:
    """Known direct-identifier columns should be detected."""
    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Customer_Name": ["Arun", "Priya"],
            "Phone_Number": ["9876543210", "9123456789"],
            "Email": ["arun@example.com", "priya@example.com"],
            "City": ["Chennai", "Madurai"],
            "Amount": [100, 200],
        }
    )

    detection = detect_identifiers(dataframe)

    assert isinstance(detection, IdentifierDetection)

    assert detection.direct_identifiers == (
        "Customer_ID",
        "Customer_Name",
        "Phone_Number",
        "Email",
    )

    assert detection.protected_columns == detection.direct_identifiers

    assert detection.safe_columns == (
        "City",
        "Amount",
    )


def test_remove_identifiers() -> None:
    """Protected identifiers should be removed from the generator input."""
    dataframe = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Customer_Name": ["Arun", "Priya"],
            "City": ["Chennai", "Madurai"],
            "Amount": [100, 200],
        }
    )

    detection = detect_identifiers(dataframe)
    protected_dataframe = remove_identifiers(dataframe, detection)

    assert list(protected_dataframe.columns) == [
        "City",
        "Amount",
    ]

    # The original dataset must not be modified.
    assert list(dataframe.columns) == [
        "Customer_ID",
        "Customer_Name",
        "City",
        "Amount",
    ]


def test_no_identifiers() -> None:
    """Datasets without known identifiers should remain unchanged."""
    dataframe = pd.DataFrame(
        {
            "City": ["Chennai", "Madurai"],
            "Amount": [100, 200],
        }
    )

    detection = detect_identifiers(dataframe)

    assert detection.direct_identifiers == ()
    assert detection.protected_columns == ()
    assert detection.safe_columns == ("City", "Amount")


def test_empty_dataset_raises_error() -> None:
    """Empty datasets should be rejected."""
    dataframe = pd.DataFrame()

    with pytest.raises(ValueError, match="empty dataset"):
        detect_identifiers(dataframe)


def test_invalid_input_raises_error() -> None:
    """Non-DataFrame input should be rejected."""
    with pytest.raises(TypeError, match="pandas DataFrame"):
        detect_identifiers({"Customer_ID": ["C001"]})

def test_generated_identifiers_do_not_overlap_large_source_dataset():
    original = pd.DataFrame(
        {
            "Customer_Name": [
                "Arun Kumar",
                "Priya Devi",
                "Rahul Raj",
                "Jegadeesh Sathaiya",
            ]
            * 25,
            "Email": [
                "arun@example.com",
                "priya@example.com",
                "rahul@example.com",
                "jegadeesh@example.com",
            ]
            * 25,
            "Age": list(range(20, 45)) * 4,
        }
    )

    detection = detect_identifiers(original)

    synthetic_safe = pd.DataFrame(
        {
            "Age": list(range(25, 125)),
        }
    )

    result = generate_fresh_identifiers(
        original_dataframe=original,
        synthetic_dataframe=synthetic_safe,
        detection=detection,
    )

    generated = result.dataframe

    for column in detection.direct_identifiers:
        original_values = set(
            original[column].dropna().astype(str)
        )

        generated_values = set(
            generated[column].dropna().astype(str)
        )

        assert original_values.isdisjoint(generated_values)