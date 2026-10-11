from pathlib import Path

from synthetic_data.jobs.results import JobResult


def test_job_result_contains_artifact_paths(tmp_path):
    synthetic_path = tmp_path / "synthetic_data.csv"
    report_path = tmp_path / "report.json"

    result = JobResult(
        job_id="job-001",
        synthetic_data_path=synthetic_path,
        report_path=report_path,
    )

    assert result.job_id == "job-001"
    assert result.synthetic_data_path == synthetic_path
    assert result.report_path == report_path


def test_job_result_is_immutable(tmp_path):
    result = JobResult(
        job_id="job-001",
        synthetic_data_path=tmp_path / "synthetic_data.csv",
        report_path=tmp_path / "report.json",
    )

    try:
        result.job_id = "job-002"
        assert False, "JobResult should be immutable"
    except AttributeError:
        pass