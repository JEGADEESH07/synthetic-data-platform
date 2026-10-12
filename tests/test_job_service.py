from datetime import datetime, timedelta, timezone
from synthetic_data.jobs.models import JobStatus
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
import pytest

def create_service(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    return JobService(repository)


def test_create_job(tmp_path):
    service = create_service(tmp_path)

    job = service.create_job(
        job_id="job-001",
        input_file="data/input.csv",
        row_count=1000,
    )

    assert job.job_id == "job-001"
    assert job.status == JobStatus.CREATED

    stored = service.get_job("job-001")

    assert stored is not None
    assert stored.status == JobStatus.CREATED


def test_queue_job(tmp_path):
    service = create_service(tmp_path)

    service.create_job(
        job_id="job-002",
        input_file="data/input.csv",
        row_count=500,
    )

    job = service.queue_job("job-002")

    assert job.status == JobStatus.QUEUED


def test_mark_running_sets_timestamp(tmp_path):
    service = create_service(tmp_path)

    service.create_job(
        job_id="job-003",
        input_file="data/input.csv",
        row_count=500,
    )

    service.queue_job("job-003")
    job = service.mark_running("job-003")

    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None


def test_mark_succeeded_sets_artifacts(tmp_path):
    service = create_service(tmp_path)

    service.create_job(
        job_id="job-004",
        input_file="data/input.csv",
        row_count=500,
    )

    service.queue_job("job-004")
    service.mark_running("job-004")

    synthetic_data_path = (
        tmp_path
        / "data"
        / "output"
        / "jobs"
        / "job-004"
        / "synthetic_data.csv"
    )
    report_path = (
        tmp_path
        / "data"
        / "output"
        / "jobs"
        / "job-004"
        / "report.json"
    )

    synthetic_data_path.parent.mkdir(parents=True, exist_ok=True)
    synthetic_data_path.write_text(
        "id,name\n1,Alice\n",
        encoding="utf-8",
    )
    report_path.write_text("{}", encoding="utf-8")

    job = service.mark_succeeded(
        job_id="job-004",
        synthetic_data_path=str(synthetic_data_path),
        report_path=str(report_path),
    )

    assert job.status == JobStatus.SUCCEEDED
    assert job.completed_at is not None
    assert job.synthetic_data_path.endswith("synthetic_data.csv")
    assert job.report_path.endswith("report.json")


def test_mark_failed_sets_error(tmp_path):
    service = create_service(tmp_path)

    service.create_job(
        job_id="job-005",
        input_file="data/input.csv",
        row_count=500,
    )

    service.queue_job("job-005")
    service.mark_running("job-005")

    job = service.mark_failed(
        job_id="job-005",
        error_code="GENERATION_FAILED",
        error_message="Generation failed.",
    )

    assert job.status == JobStatus.FAILED
    assert job.completed_at is not None
    assert job.error_code == "GENERATION_FAILED"
    assert job.error_message == "Generation failed."


def test_cannot_skip_job_lifecycle(tmp_path):
    service = create_service(tmp_path)

    service.create_job(
        job_id="job-006",
        input_file="data/input.csv",
        row_count=500,
    )

    try:
        service.mark_running("job-006")
    except ValueError as exc:
        assert "expected QUEUED" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

def test_fail_stale_job_marks_old_running_job_failed(tmp_path):
    service = create_service(tmp_path)

    job = service.create_job(
        job_id="stale-job",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    service.queue_job(job.job_id)
    service.mark_running(job.job_id)

    job = service.get_job(job.job_id)
    job.started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    service.repository.update(job)

    failed_job = service.fail_stale_job(
        job.job_id,
        stale_after_seconds=60,
    )

    assert failed_job.status == JobStatus.FAILED
    assert failed_job.execution_stage == "FAILED"
    assert failed_job.error_code == "STALE_JOB"
    assert failed_job.completed_at is not None

def test_fail_stale_job_rejects_fresh_running_job(tmp_path):
    service = create_service(tmp_path)

    job = service.create_job(
        job_id="fresh-job",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    service.queue_job(job.job_id)
    service.mark_running(job.job_id)

    with pytest.raises(ValueError, match="Job is not stale"):
        service.fail_stale_job(
            job.job_id,
            stale_after_seconds=60,
        )

def test_unknown_job_returns_none(tmp_path):
    service = create_service(tmp_path)

    assert service.get_job("does-not-exist") is None