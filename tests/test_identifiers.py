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

def test_detect_generic_identifier_columns() -> None:
    """Common entity ID columns should be detected."""
    dataframe = pd.DataFrame(
        {
            "employee_id": ["E001", "E002"],
            "manager_id": ["M001", "M002"],
            "order_id": ["O001", "O002"],
            "transaction_id": ["T001", "T002"],
            "department": ["Engineering", "Finance"],
            "salary": [500000, 700000],
        }
    )

    detection = detect_identifiers(dataframe)

    assert detection.direct_identifiers == (
        "employee_id",
        "manager_id",
        "order_id",
        "transaction_id",
    )

    assert detection.protected_columns == detection.direct_identifiers

    assert detection.safe_columns == (
        "department",
        "salary",
    )

def test_generate_fresh_generic_identifiers() -> None:
    """Generic ID columns should receive fresh non-overlapping values."""
    original = pd.DataFrame(
        {
            "employee_id": ["EMP001", "EMP002", "EMP003"],
            "department": ["Engineering", "Finance", "HR"],
        }
    )

    synthetic_safe = pd.DataFrame(
        {
            "department": ["Engineering", "Sales", "HR", "Finance"],
        }
    )

    detection = detect_identifiers(original)

    result = generate_fresh_identifiers(
        original_dataframe=original,
        synthetic_dataframe=synthetic_safe,
        detection=detection,
    )

    generated = result.dataframe

    assert "employee_id" in generated.columns
    assert len(generated) == 4
    assert generated["employee_id"].is_unique

    original_ids = set(original["employee_id"])
    generated_ids = set(generated["employee_id"])

    assert original_ids.isdisjoint(generated_ids)

    assert result.generated_columns == ("employee_id",)