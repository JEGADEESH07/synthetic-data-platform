"""Tests for privacy evaluation."""

import pandas as pd
import pytest

from synthetic_data.identifiers import detect_identifiers
from synthetic_data.privacy import (
    PrivacyEvaluationError,
    evaluate_privacy,
)


def build_detection(dataframe: pd.DataFrame):
    """Build identifier detection for the test dataset."""
    return detect_identifiers(dataframe)


def test_no_identifier_overlap_passes():
    """No exact protected-value overlap should pass."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
                "C003",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
                "Charlie",
            ],
            "Age": [
                25,
                30,
                35,
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
                "S002",
                "S003",
            ],
            "Customer_Name": [
                "David",
                "Emma",
                "Frank",
            ],
            "Age": [
                26,
                31,
                36,
            ],
        }
    )

    detection = build_detection(source)

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "PASS"

    assert report.total_exact_matches == 0

    assert report.matched_columns == ()

    assert report.duplicates.duplicate_row_count == 0

    assert report.duplicates.duplicate_row_rate == 0.0


def test_exact_identifier_overlap_fails():
    """Exact protected-value overlap must fail privacy evaluation."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
                "C003",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
                "Charlie",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
                "C002",
                "S003",
            ],
            "Customer_Name": [
                "David",
                "Emma",
                "Frank",
            ],
        }
    )

    detection = build_detection(source)

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "FAIL"

    assert report.total_exact_matches == 1

    assert report.matched_columns == (
        "Customer_ID",
    )

    customer_id_result = next(
        result
        for result in report.identifier_results
        if result.column_name == "Customer_ID"
    )

    assert customer_id_result.exact_match_count == 1

    assert customer_id_result.exact_match_rate == pytest.approx(
        1 / 3
    )


def test_multiple_identifier_overlaps_are_detected():
    """Overlaps across multiple protected columns are reported."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
            ],
            "Phone_Number": [
                "9000000001",
                "9000000002",
            ],
            "Email": [
                "alice@example.com",
                "bob@example.com",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "S002",
            ],
            "Customer_Name": [
                "Alice",
                "Emma",
            ],
            "Phone_Number": [
                "9000000001",
                "9111111111",
            ],
            "Email": [
                "new@example.com",
                "bob@example.com",
            ],
        }
    )

    detection = build_detection(source)

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "FAIL"

    assert report.total_exact_matches == 4

    assert set(report.matched_columns) == {
        "Customer_ID",
        "Customer_Name",
        "Phone_Number",
        "Email",
    }

    # Customer_ID = 1
    # Customer_Name = 1
    # Phone_Number = 1
    # Email = 1
    assert report.total_exact_matches == 4


def test_duplicate_synthetic_rows_require_review():
    """Duplicate synthetic rows should require review."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
                "C003",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
                "Charlie",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
                "S002",
                "S002",
                "S003",
            ],
            "Customer_Name": [
                "David",
                "Emma",
                "Emma",
                "Frank",
            ],
        }
    )

    detection = build_detection(source)

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "REVIEW_REQUIRED"

    assert report.total_exact_matches == 0

    assert report.duplicates.duplicate_row_count == 2

    assert report.duplicates.duplicate_row_rate == pytest.approx(
        0.5
    )


def test_exact_overlap_takes_priority_over_duplicate_review():
    """Exact identifier overlap must result in FAIL."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C001",
            ],
            "Customer_Name": [
                "Alice",
                "Alice",
            ],
        }
    )

    detection = build_detection(source)

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "FAIL"

    assert report.total_exact_matches == 2

    assert report.duplicates.duplicate_row_count == 2


def test_empty_source_dataset_raises_error():
    """An empty source dataset cannot be evaluated."""

    source = pd.DataFrame(
        {
            "Customer_ID": [],
            "Customer_Name": [],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": ["S001"],
            "Customer_Name": ["Alice"],
        }
    )

    detection = build_detection(
        pd.DataFrame(
            {
                "Customer_ID": ["C001"],
                "Customer_Name": ["Bob"],
            }
        )
    )

    with pytest.raises(PrivacyEvaluationError):
        evaluate_privacy(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            detection=detection,
        )


def test_empty_synthetic_dataset_raises_error():
    """An empty synthetic dataset cannot be evaluated."""

    source = pd.DataFrame(
        {
            "Customer_ID": ["C001"],
            "Customer_Name": ["Alice"],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [],
            "Customer_Name": [],
        }
    )

    detection = build_detection(source)

    with pytest.raises(PrivacyEvaluationError):
        evaluate_privacy(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            detection=detection,
        )


def test_missing_identifier_column_in_synthetic_raises_error():
    """Missing protected columns must fail evaluation."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
            ],
            "Customer_Name": [
                "Alice",
                "Bob",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_Name": [
                "Charlie",
                "David",
            ],
        }
    )

    detection = build_detection(source)

    with pytest.raises(PrivacyEvaluationError):
        evaluate_privacy(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            detection=detection,
        )


def test_invalid_source_type_raises_error():
    """The evaluator must reject invalid source input."""

    source = [
        {
            "Customer_ID": "C001",
        }
    ]

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
            ],
        }
    )

    detection_source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
            ],
        }
    )

    detection = build_detection(
        detection_source
    )

    with pytest.raises(TypeError):
        evaluate_privacy(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            detection=detection,
        )


def test_invalid_detection_type_raises_error():
    """The evaluator must require IdentifierDetection."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
            ],
        }
    )

    with pytest.raises(TypeError):
        evaluate_privacy(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            detection=None,
        )


def test_no_protected_identifiers_requires_review():
    """Datasets without protected identifiers must not pass privacy review."""

    source = pd.DataFrame(
        {
            "Age": [24, 31, 28, 35],
            "City": ["Chennai", "Madurai", "Trichy", "Salem"],
            "Amount": [1200, 2400, 1800, 3200],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [25, 32, 29, 36],
            "City": ["Coimbatore", "Chennai", "Salem", "Madurai"],
            "Amount": [1300, 2500, 1900, 3300],
        }
    )

    detection = build_detection(source)
    assert not detection.direct_identifiers

    report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    assert report.status == "REVIEW_REQUIRED"
    assert report.identifier_results == ()
    assert report.total_exact_matches == 0
