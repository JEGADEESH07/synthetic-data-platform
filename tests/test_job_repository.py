import sqlite3
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


def test_repository_adds_progress_and_input_columns_to_existing_database(
    tmp_path,
):
    database_path = tmp_path / "jobs.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                input_file TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                synthetic_data_path TEXT,
                report_path TEXT,
                error_code TEXT,
                error_message TEXT
            )
            """
        )

    repository = JobRepository(str(database_path))

    job = create_job()
    job.input_columns = 15
    job.execution_stage = "generating"
    job.progress = 40
    job.completed_units = 4
    job.total_units = 10

    repository.create(job)

    stored_job = repository.get(job.job_id)

    assert stored_job is not None
    assert stored_job.input_columns == 15
    assert stored_job.execution_stage == "generating"
    assert stored_job.progress == 40
    assert stored_job.completed_units == 4
    assert stored_job.total_units == 10


def test_repository_creates_and_gets_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    job = create_job()
    job.input_columns = 15
    job.execution_stage = "generating"
    job.progress = 40
    job.completed_units = 4
    job.total_units = 10

    repository.create(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.job_id == "job-001"
    assert stored_job.input_file == "data/input.csv"
    assert stored_job.row_count == 1000
    assert stored_job.status == JobStatus.CREATED
    assert stored_job.input_columns == 15
    assert stored_job.execution_stage == "generating"
    assert stored_job.progress == 40
    assert stored_job.completed_units == 4
    assert stored_job.total_units == 10


def test_repository_returns_none_for_unknown_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    assert repository.get("does-not-exist") is None


def test_repository_updates_job(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    job = create_job()
    repository.create(job)

    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    job.input_columns = 15
    job.execution_stage = "validating"
    job.progress = 25
    job.completed_units = 1
    job.total_units = 4

    repository.update(job)

    stored_job = repository.get("job-001")

    assert stored_job is not None
    assert stored_job.status == JobStatus.RUNNING
    assert stored_job.started_at is not None
    assert stored_job.input_columns == 15
    assert stored_job.execution_stage == "validating"
    assert stored_job.progress == 25
    assert stored_job.completed_units == 1
    assert stored_job.total_units == 4


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

def test_repository_persists_execution_metadata(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    job.execution_metadata = {
        "schema_version": "1.0",
        "engine": {"name": "V0.2", "version": "0.2.0"},
        "seed": 42,
    }

    repository.create(job)
    stored_job = repository.get(job.job_id)

    assert stored_job is not None
    assert stored_job.execution_metadata == job.execution_metadata


def test_repository_updates_execution_metadata(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()
    repository.create(job)

    job.execution_metadata = {"seed": 123, "outcome": "SUCCEEDED"}
    repository.update(job)

    stored_job = repository.get(job.job_id)

    assert stored_job is not None
    assert stored_job.execution_metadata == job.execution_metadata


def test_repository_preserves_missing_execution_metadata(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))
    job = create_job()

    repository.create(job)
    stored_job = repository.get(job.job_id)

    assert stored_job is not None
    assert stored_job.execution_metadata is None


def test_repository_lists_jobs_by_status(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    queued_job = create_job("queued-job")
    queued_job.status = JobStatus.QUEUED
    repository.create(queued_job)

    running_job = create_job("running-job")
    running_job.status = JobStatus.RUNNING
    repository.create(running_job)

    queued_jobs = repository.list_by_status(JobStatus.QUEUED)

    assert [job.job_id for job in queued_jobs] == ["queued-job"]
    assert queued_jobs[0].status == JobStatus.QUEUED


def test_repository_lists_all_jobs_newest_first(tmp_path):
    repository = JobRepository(str(tmp_path / "jobs.db"))

    older_job = create_job("older-job")
    older_job.created_at = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    )

    newer_job = create_job("newer-job")
    newer_job.created_at = datetime(
        2026, 1, 2, tzinfo=timezone.utc
    )

    repository.create(older_job)
    repository.create(newer_job)

    jobs = repository.list_all()

    assert [job.job_id for job in jobs] == [
        "newer-job",
        "older-job",
    ]
