import pandas as pd
import pytest

from synthetic_data.validation import (
    SchemaValidationError,
    validate_schema,
)


def test_valid_schema():
    source = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Age": [25, 30],
            "Amount": [1000, 2000],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": ["SYN_001", "SYN_002"],
            "Age": [27, 32],
            "Amount": [1200, 1900],
        }
    )

    result = validate_schema(
        source,
        synthetic,
    )

    assert result.valid is True
    assert result.row_count == 2
    assert result.column_count == 3


def test_rejects_missing_column():
    source = pd.DataFrame(
        {
            "Customer_ID": ["C001"],
            "Age": [25],
            "Amount": [1000],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": ["SYN_001"],
            "Age": [27],
        }
    )

    with pytest.raises(SchemaValidationError):
        validate_schema(source, synthetic)


def test_rejects_wrong_column_order():
    source = pd.DataFrame(
        {
            "Customer_ID": ["C001"],
            "Age": [25],
            "Amount": [1000],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [27],
            "Customer_ID": ["SYN_001"],
            "Amount": [1200],
        }
    )

    with pytest.raises(SchemaValidationError):
        validate_schema(source, synthetic)


def test_rejects_empty_dataset():
    source = pd.DataFrame(
        {
            "Customer_ID": ["C001"],
            "Age": [25],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [],
            "Age": [],
        }
    )

    with pytest.raises(SchemaValidationError):
        validate_schema(source, synthetic)