
"""Tests for statistical quality evaluation."""

import pandas as pd
import pytest

from synthetic_data.evaluation import (
    StatisticalEvaluationError,
    evaluate_statistical_quality,
)
from synthetic_data.identifiers import detect_identifiers
from synthetic_data.metadata import build_metadata_policy


def build_policy(dataframe: pd.DataFrame):
    """Build the metadata policy used by the evaluator."""
    detection = detect_identifiers(dataframe)

    return build_metadata_policy(
        dataframe,
        detection,
    )


def test_identical_numerical_and_categorical_data_scores_one():
    """Identical trainable columns should receive perfect quality."""

    source = pd.DataFrame(
        {
            "Age": [20, 25, 30, 35, 40],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
                "Coimbatore",
                "Madurai",
            ],
        }
    )

    synthetic = source.copy()

    policy = build_policy(source)

    report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        policy=policy,
    )

    assert report.overall_score == pytest.approx(1.0)

    assert len(report.columns) == 2

    assert report.columns[0].column_name == "Age"
    assert report.columns[0].score == pytest.approx(1.0)

    assert report.columns[1].column_name == "City"
    assert report.columns[1].score == pytest.approx(1.0)

    assert report.passed_columns == (
        "Age",
        "City",
    )

    assert report.failed_columns == ()


def test_distribution_difference_reduces_quality_score():
    """Different distributions should reduce statistical quality."""

    source = pd.DataFrame(
        {
            "Age": [20, 25, 30, 35, 40],
            "City": [
                "Chennai",
                "Chennai",
                "Chennai",
                "Madurai",
                "Madurai",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [50, 55, 60, 65, 70],
            "City": [
                "Delhi",
                "Delhi",
                "Mumbai",
                "Mumbai",
                "Mumbai",
            ],
        }
    )

    policy = build_policy(source)

    report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        policy=policy,
    )

    assert report.overall_score < 1.0

    assert "Age" in report.failed_columns
    assert "City" in report.failed_columns


def test_protected_columns_are_excluded_from_quality_evaluation():
    """Protected identifiers must not be treated as statistical targets."""

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
            "City": [
                "Chennai",
                "Chennai",
                "Madurai",
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
                "Xavier",
                "Yamini",
                "Rahul",
            ],
            "Age": [
                25,
                30,
                35,
            ],
            "City": [
                "Chennai",
                "Chennai",
                "Madurai",
            ],
        }
    )

    policy = build_policy(source)

    report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        policy=policy,
    )

    evaluated_columns = tuple(
        result.column_name
        for result in report.columns
    )

    assert evaluated_columns == (
        "Age",
        "City",
    )

    assert "Customer_ID" not in evaluated_columns
    assert "Customer_Name" not in evaluated_columns

    assert report.overall_score == pytest.approx(1.0)


def test_missing_trainable_column_in_source_raises_error():
    """Missing policy columns in the source must fail evaluation."""

    source = pd.DataFrame(
        {
            "Age": [20, 25, 30],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [21, 26, 31],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
            ],
        }
    )

    policy = build_policy(source)

    # Create a policy based on a dataset that contains an
    # additional trainable column.
    policy_source = pd.DataFrame(
        {
            "Age": [20, 25, 30],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
            ],
            "Income": [
                25000,
                35000,
                45000,
            ],
        }
    )

    policy = build_policy(policy_source)

    with pytest.raises(StatisticalEvaluationError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_missing_trainable_column_in_synthetic_raises_error():
    """Missing policy columns in synthetic data must fail evaluation."""

    source = pd.DataFrame(
        {
            "Age": [20, 25, 30],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [21, 26, 31],
        }
    )

    policy = build_policy(source)

    with pytest.raises(StatisticalEvaluationError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_schema_difference_is_not_required_for_protected_columns():
    """Protected columns may differ because they are regenerated."""

    source = pd.DataFrame(
        {
            "Customer_ID": [
                "C001",
                "C002",
                "C003",
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
            "Age": [
                25,
                30,
                35,
            ],
        }
    )

    policy = build_policy(source)

    report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        policy=policy,
    )

    assert len(report.columns) == 1
    assert report.columns[0].column_name == "Age"
    assert report.overall_score == pytest.approx(1.0)


def test_empty_source_dataset_raises_error():
    """An empty source dataset cannot be evaluated."""

    source = pd.DataFrame(
        {
            "Age": [],
            "City": [],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [20, 25],
            "City": [
                "Chennai",
                "Madurai",
            ],
        }
    )

    policy = build_policy(
        pd.DataFrame(
            {
                "Age": [20, 25],
                "City": [
                    "Chennai",
                    "Madurai",
                ],
            }
        )
    )

    with pytest.raises(StatisticalEvaluationError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_empty_synthetic_dataset_raises_error():
    """An empty synthetic dataset cannot be evaluated."""

    source = pd.DataFrame(
        {
            "Age": [20, 25, 30],
            "City": [
                "Chennai",
                "Madurai",
                "Chennai",
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [],
            "City": [],
        }
    )

    policy = build_policy(source)

    with pytest.raises(StatisticalEvaluationError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_invalid_source_dataframe_type_raises_error():
    """The evaluator must reject non-DataFrame source input."""

    source = [
        {"Age": 20}
    ]

    synthetic = pd.DataFrame(
        {
            "Age": [25],
        }
    )

    policy_source = pd.DataFrame(
        {
            "Age": [20],
        }
    )

    policy = build_policy(policy_source)

    with pytest.raises(TypeError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_invalid_synthetic_dataframe_type_raises_error():
    """The evaluator must reject non-DataFrame synthetic input."""

    source = pd.DataFrame(
        {
            "Age": [20, 25],
        }
    )

    synthetic = [
        {"Age": 30}
    ]

    policy = build_policy(source)

    with pytest.raises(TypeError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=policy,
        )


def test_invalid_policy_type_raises_error():
    """The evaluator must require a MetadataPolicy."""

    source = pd.DataFrame(
        {
            "Age": [20, 25],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Age": [21, 26],
        }
    )

    with pytest.raises(TypeError):
        evaluate_statistical_quality(
            source_dataframe=source,
            synthetic_dataframe=synthetic,
            policy=None,
        )


@pytest.mark.parametrize(
    "source",
    [
        # Numerical columns
        pd.DataFrame({"Age": [18, 25, 40, 65]}),
        # Categorical column with several distinct values
        pd.DataFrame({"City": ["Chennai", "Madurai", "Salem", "Trichy"]}),
        # Boolean column
        pd.DataFrame({"Active": [True, False, True, False]}),
        # Mixed numerical, categorical, and boolean columns
        pd.DataFrame(
            {
                "Age": [18, 25, 40, 65],
                "City": ["Chennai", "Madurai", "Salem", "Trichy"],
                "Active": [True, False, True, False],
            }
        ),
    ],
    ids=[
        "numerical-only",
        "categorical-only",
        "boolean-only",
        "mixed-columns",
    ],
)
def test_identical_data_quality_across_dataset_shapes(source):
    """Identical source and synthetic data should score perfectly."""
    synthetic = source.copy()
    policy = build_policy(source)

    report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        policy=policy,
    )

    assert report.overall_score == pytest.approx(1.0)
    assert report.failed_columns == ()
