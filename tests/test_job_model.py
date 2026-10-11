from datetime import datetime, timezone

from synthetic_data.jobs.models import Job, JobStatus


def test_job_defaults_to_created():
    job = Job(
        job_id="job-001",
        input_file="data/input.csv",
        row_count=1000,
    )

    assert job.status == JobStatus.CREATED
    assert job.job_id == "job-001"
    assert job.input_file == "data/input.csv"
    assert job.row_count == 1000
    assert isinstance(job.created_at, datetime)
    assert job.created_at.tzinfo == timezone.utc


def test_job_status_values():
    assert JobStatus.CREATED.value == "CREATED"
    assert JobStatus.QUEUED.value == "QUEUED"
    assert JobStatus.RUNNING.value == "RUNNING"
    assert JobStatus.SUCCEEDED.value == "SUCCEEDED"
    assert JobStatus.FAILED.value == "FAILED"


def test_job_artifacts_default_to_none():
    job = Job(
        job_id="job-002",
        input_file="data/input.csv",
        row_count=500,
    )

    assert job.synthetic_data_path is None
    assert job.report_path is None


def test_job_error_fields_default_to_none():
    job = Job(
        job_id="job-003",
        input_file="data/input.csv",
        row_count=500,
    )

    assert job.error_code is None
    assert job.error_message is None


def test_job_can_store_success_information():
    job = Job(
        job_id="job-004",
        input_file="data/input.csv",
        row_count=1000,
    )

    job.status = JobStatus.SUCCEEDED
    job.started_at = datetime.now(timezone.utc)
    job.completed_at = datetime.now(timezone.utc)
    job.synthetic_data_path = (
        "data/output/jobs/job-004/synthetic_data.csv"
    )
    job.report_path = "data/output/jobs/job-004/report.json"

    assert job.status == JobStatus.SUCCEEDED
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.synthetic_data_path.endswith("synthetic_data.csv")
    assert job.report_path.endswith("report.json")


def test_job_can_store_failure_information():
    job = Job(
        job_id="job-005",
        input_file="data/input.csv",
        row_count=1000,
    )

    job.status = JobStatus.FAILED
    job.error_code = "GENERATION_FAILED"
    job.error_message = "Synthetic data generation failed."

    assert job.status == JobStatus.FAILED
    assert job.error_code == "GENERATION_FAILED"
    assert job.error_message == "Synthetic data generation failed."