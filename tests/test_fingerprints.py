
import pandas as pd

from synthetic_data.audit.fingerprints import (
    fingerprint_dataset,
    fingerprint_schema,
)


def test_schema_fingerprint_is_stable():
    dataframe = pd.DataFrame({
        "age": [21, 25],
        "city": ["Chennai", "Madurai"],
    })

    assert fingerprint_schema(dataframe) == fingerprint_schema(dataframe)


def test_schema_fingerprint_changes_when_column_order_changes():
    first = pd.DataFrame({
        "age": [21],
        "city": ["Chennai"],
    })
    reordered = first[["city", "age"]]

    assert fingerprint_schema(first) != fingerprint_schema(reordered)


def test_schema_fingerprint_changes_when_dtype_changes():
    integers = pd.DataFrame({"value": [1, 2]})
    strings = pd.DataFrame({"value": ["1", "2"]})

    assert fingerprint_schema(integers) != fingerprint_schema(strings)


def test_dataset_fingerprint_is_stable():
    dataframe = pd.DataFrame({
        "id": [1, 2, 3],
        "amount": [100.5, 200.0, 75.25],
    })

    assert fingerprint_dataset(dataframe) == fingerprint_dataset(dataframe)


def test_dataset_fingerprint_changes_when_values_change():
    original = pd.DataFrame({"amount": [100, 200]})
    changed = pd.DataFrame({"amount": [100, 201]})

    assert fingerprint_dataset(original) != fingerprint_dataset(changed)


def test_dataset_fingerprint_changes_when_row_order_changes():
    original = pd.DataFrame({"value": [10, 20, 30]})
    reordered = original.iloc[[2, 1, 0]]

    assert fingerprint_dataset(original) != fingerprint_dataset(reordered)


def test_dataset_fingerprint_changes_when_schema_changes():
    original = pd.DataFrame({"amount": [100, 200]})
    extended = pd.DataFrame({
        "amount": [100, 200],
        "currency": ["INR", "INR"],
    })

    assert fingerprint_dataset(original) != fingerprint_dataset(extended)
