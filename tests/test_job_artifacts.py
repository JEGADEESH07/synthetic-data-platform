from pathlib import Path

import pytest

from synthetic_data.jobs.artifacts import (
    ArtifactManager,
    ArtifactNotFoundError,
)


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