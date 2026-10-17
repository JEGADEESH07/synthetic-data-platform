"""Tests for output persistence."""

import json

import pandas as pd
import pytest

from synthetic_data.identifiers import detect_identifiers
from synthetic_data.persistence import (
    ArtifactPersistenceError,
    persist_artifacts,
)
from synthetic_data.privacy import evaluate_privacy
from synthetic_data.validation import validate_schema
from synthetic_data.evaluation import evaluate_statistical_quality
from synthetic_data.metadata import build_metadata_policy

def build_test_results():
    """Create valid evaluation objects for persistence tests."""

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
            "Age": [
                25,
                30,
            ],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": [
                "S001",
                "S002",
            ],
            "Customer_Name": [
                "Charlie",
                "David",
            ],
            "Age": [
                26,
                31,
            ],
        }
    )

    detection = detect_identifiers(source)

    schema_result = validate_schema(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
    )

    privacy_report = evaluate_privacy(
        source_dataframe=source,
        synthetic_dataframe=synthetic,
        detection=detection,
    )

    return (
        synthetic,
        schema_result,
        privacy_report,
    )


def test_persist_artifacts_creates_files(tmp_path):
    """Persistence should create the expected artifact files."""

    (
        synthetic,
        schema_result,
        privacy_report,
    ) = build_test_results()

    artifacts = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_test_001",
    )

    assert artifacts.job_id == "job_test_001"

    assert artifacts.output_directory.exists()

    assert artifacts.synthetic_data_path.exists()

    assert artifacts.report_path.exists()


def test_persisted_csv_can_be_read_back(tmp_path):
    """Persisted CSV should contain the synthetic dataset."""

    (
        synthetic,
        schema_result,
        privacy_report,
    ) = build_test_results()

    artifacts = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_test_csv",
    )

    loaded = pd.read_csv(
        artifacts.synthetic_data_path
    )

    assert list(loaded.columns) == list(
        synthetic.columns
    )

    assert len(loaded) == len(synthetic)


def test_persisted_report_contains_evaluation(
    tmp_path,
):
    """Persisted report should contain evaluation information."""

    (
        synthetic,
        schema_result,
        privacy_report,
    ) = build_test_results()

    artifacts = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_test_report",
    )

    report = json.loads(
        artifacts.report_path.read_text(
            encoding="utf-8"
        )
    )

    assert report["job_id"] == "job_test_report"

    assert report["synthetic_data"]["row_count"] == 2

    assert report["schema_validation"]["valid"] is True

    assert report["privacy"]["status"] == "PASS"

    assert report["privacy"]["total_exact_matches"] == 0


def test_empty_synthetic_dataset_is_rejected(
    tmp_path,
):
    """Empty synthetic data must not be persisted."""

    (
        _,
        schema_result,
        privacy_report,
    ) = build_test_results()

    empty = pd.DataFrame(
        columns=[
            "Customer_ID",
            "Customer_Name",
            "Age",
        ]
    )

    with pytest.raises(
        ArtifactPersistenceError
    ):
        persist_artifacts(
            synthetic_dataframe=empty,
            schema_result=schema_result,
            privacy_report=privacy_report,
            output_root=tmp_path,
        )


def test_existing_job_directory_is_rejected(
    tmp_path,
):
    """A job ID must not silently overwrite an existing run."""

    (
        synthetic,
        schema_result,
        privacy_report,
    ) = build_test_results()

    first = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_duplicate",
    )

    assert first.output_directory.exists()

    with pytest.raises(
        ArtifactPersistenceError
    ):
        persist_artifacts(
            synthetic_dataframe=synthetic,
            schema_result=schema_result,
            privacy_report=privacy_report,
            output_root=tmp_path,
            job_id="job_duplicate",
        )


def test_persisted_report_contains_audit_metadata(tmp_path):
    """Persisted report should preserve supplied audit metadata."""

    synthetic, schema_result, privacy_report = build_test_results()

    audit_metadata = {
        "engine": {
            "engine_name": "V0.2 single-table synthesis engine",
            "engine_version": "0.2.0",
        },
        "reproducibility": {
            "seed": 42,
        },
    }

    artifacts = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_test_audit",
        audit_metadata=audit_metadata,
    )

    report = json.loads(
        artifacts.report_path.read_text(encoding="utf-8")
    )

    assert report["audit"] == audit_metadata


def test_persisted_report_contains_statistical_quality(tmp_path):
    """Persisted report should include statistical quality results."""

    synthetic, schema_result, privacy_report = build_test_results()

    source = pd.DataFrame(
        {
            "Age": [25, 30],
        }
    )
    synthetic_quality_data = synthetic[["Age"]].copy()

    detection = detect_identifiers(source)
    policy = build_metadata_policy(source, detection)

    quality_report = evaluate_statistical_quality(
        source_dataframe=source,
        synthetic_dataframe=synthetic_quality_data,
        policy=policy,
    )

    artifacts = persist_artifacts(
        synthetic_dataframe=synthetic,
        schema_result=schema_result,
        privacy_report=privacy_report,
        output_root=tmp_path,
        job_id="job_test_quality",
        statistical_quality_report=quality_report,
    )

    report = json.loads(
        artifacts.report_path.read_text(encoding="utf-8")
    )
    quality = report["statistical_quality_report"]

    assert quality["overall_score"] == pytest.approx(
        quality_report.overall_score
    )
    assert quality["minimum_score"] == pytest.approx(
        quality_report.minimum_score
    )
    assert quality["passed_columns"] == list(
        quality_report.passed_columns
    )
    assert quality["failed_columns"] == list(
        quality_report.failed_columns
    )
    assert len(quality["columns"]) == len(quality_report.columns)
    assert quality["columns"][0]["column_name"] == "Age"
    assert quality["columns"][0]["score"] == pytest.approx(
        quality_report.columns[0].score
    )
    assert "details" in quality["columns"][0]
