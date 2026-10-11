from datetime import datetime, timezone

from synthetic_data.jobs.models import Job, JobStatus
from synthetic_data.jobs.repository import JobRepository


def create_job(job_id: str = "job-001") -> Job:
    return Job(
        job_id=job_id,
        input_file="data/input.csv",
        row_count=1000,
    )


def test_repository_creates_database(tmp_path):
    database_path = tmp_path / "jobs.db"

    JobRepository(str(database_path))

    assert database_path.exists()


def test_repository_creates_and_gets_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    repository.create(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.job_id == "job-001"
    assert stored_job.input_file == "data/input.csv"
    assert stored_job.row_count == 1000
    assert stored_job.status == JobStatus.CREATED


def test_repository_returns_none_for_unknown_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    assert repository.get("does-not-exist") is None


def test_repository_updates_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    repository.create(job)

    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)

    repository.update(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.status == JobStatus.RUNNING
    assert stored_job.started_at is not None


def test_repository_persists_success_artifacts(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    repository.create(job)

    job.status = JobStatus.SUCCEEDED
    job.synthetic_data_path = (
        "data/output/jobs/job-001/synthetic_data.csv"
    )
    job.report_path = "data/output/jobs/job-001/report.json"
    job.completed_at = datetime.now(timezone.utc)

    repository.update(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.status == JobStatus.SUCCEEDED
    assert stored_job.synthetic_data_path.endswith("synthetic_data.csv")
    assert stored_job.report_path.endswith("report.json")
    assert stored_job.completed_at is not None


def test_repository_persists_failure_information(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    repository.create(job)

    job.status = JobStatus.FAILED
    job.error_code = "GENERATION_FAILED"
    job.error_message = "Generation failed."

    repository.update(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.status == JobStatus.FAILED
    assert stored_job.error_code == "GENERATION_FAILED"
    assert stored_job.error_message == "Generation failed."