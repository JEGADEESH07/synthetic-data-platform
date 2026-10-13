from pathlib import Path

import pandas as pd
import pytest

from synthetic_data.jobs.artifacts import (
    ArtifactManager,
    ArtifactNotFoundError,
)
from synthetic_data.persistence import (
    ArtifactPersistenceError,
    persist_artifacts,
)
from synthetic_data.privacy.evaluator import (
    DuplicatePrivacyResult,
    PrivacyReport,
)
from synthetic_data.validation import SchemaValidationResult

def test_get_artifacts(tmp_path):
    job_directory = tmp_path / "job-001"
    job_directory.mkdir()

    synthetic_path = job_directory / "synthetic_data.csv"
    report_path = job_directory / "report.json"

    synthetic_path.write_text("id,value\n1,100\n", encoding="utf-8")
    report_path.write_text('{"status": "PASS"}', encoding="utf-8")

    manager = ArtifactManager(tmp_path)

    artifacts = manager.get_artifacts("job-001")

    assert artifacts.job_id == "job-001"
    assert artifacts.output_directory == job_directory
    assert artifacts.synthetic_data_path == synthetic_path
    assert artifacts.report_path == report_path


def test_missing_job_artifacts_raise_error(tmp_path):
    manager = ArtifactManager(tmp_path)

    with pytest.raises(
        ArtifactNotFoundError,
        match="Artifacts not found",
    ):
        manager.get_artifacts("job-001")


def test_missing_synthetic_data_raises_error(tmp_path):
    job_directory = tmp_path / "job-001"
    job_directory.mkdir()

    (job_directory / "report.json").write_text(
        "{}",
        encoding="utf-8",
    )

    manager = ArtifactManager(tmp_path)

    with pytest.raises(
        ArtifactNotFoundError,
        match="Synthetic data artifact not found",
    ):
        manager.get_artifacts("job-001")


def test_missing_report_raises_error(tmp_path):
    job_directory = tmp_path / "job-001"
    job_directory.mkdir()

    (job_directory / "synthetic_data.csv").write_text(
        "id,value\n1,100\n",
        encoding="utf-8",
    )

    manager = ArtifactManager(tmp_path)

    with pytest.raises(
        ArtifactNotFoundError,
        match="Report artifact not found",
    ):
        manager.get_artifacts("job-001")

def test_persist_artifacts_cleans_partial_output_on_failure(
    tmp_path,
    monkeypatch,
):
    synthetic_dataframe = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    )

    schema_result = SchemaValidationResult(
        valid=True,
        row_count=2,
        column_count=2,
        columns=["id", "name"],
    )

    privacy_report = PrivacyReport(
    status="PASS",
    identifier_results=(),
    duplicates=DuplicatePrivacyResult(
        duplicate_row_count=0,
        duplicate_row_rate=0.0,
    ),
    )

    def fail_write_text(*args, **kwargs):
        raise OSError("simulated report write failure")

    monkeypatch.setattr(
        Path,
        "write_text",
        fail_write_text,
    )

    output_root = tmp_path / "jobs"

    with pytest.raises(ArtifactPersistenceError):
        persist_artifacts(
            synthetic_dataframe=synthetic_dataframe,
            schema_result=schema_result,
            privacy_report=privacy_report,
            output_root=output_root,
            job_id="cleanup-test",
        )

    assert not (output_root / "cleanup-test").exists()

def test_job_id_cannot_escape_output_root(tmp_path):
    output_root = tmp_path / "jobs"
    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()

    (outside_directory / "synthetic_data.csv").write_text(
        "id,value\n1,100\n",
        encoding="utf-8",
    )
    (outside_directory / "report.json").write_text(
        '{"status": "PASS"}',
        encoding="utf-8",
    )

    manager = ArtifactManager(output_root)

    with pytest.raises(ArtifactNotFoundError):
        manager.get_artifacts("../outside")
