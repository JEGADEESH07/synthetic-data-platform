from synthetic_data.jobs.models import JobStatus
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.runtime import Worker


def create_worker(tmp_path, executor):
    repository = JobRepository(tmp_path / "jobs.db")
    service = JobService(repository)
    queue = JobQueue()

    job = service.create_job(
        job_id="job-001",
        input_file="input.csv",
        row_count=100,
    )

    service.queue_job(job.job_id)
    queue.enqueue(job.job_id)

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=executor,
    )

    return worker, service


def test_worker_processes_job_successfully(tmp_path):
    def executor(job_id):
        assert job_id == "job-001"
        return "synthetic_data.csv", "report.json"

    worker, service = create_worker(tmp_path, executor)

    processed_job_id = worker.run_once()

    assert processed_job_id == "job-001"

    job = service.get_job("job-001")

    assert job.status == JobStatus.SUCCEEDED
    assert job.synthetic_data_path == "synthetic_data.csv"
    assert job.report_path == "report.json"
    assert job.started_at is not None
    assert job.completed_at is not None


def test_worker_handles_execution_failure(tmp_path):
    def executor(job_id):
        raise RuntimeError("generation failed")

    worker, service = create_worker(tmp_path, executor)

    processed_job_id = worker.run_once()

    assert processed_job_id == "job-001"

    job = service.get_job("job-001")

    assert job.status == JobStatus.FAILED
    assert job.error_code == "JOB_EXECUTION_FAILED"
    assert job.error_message == "generation failed"
    assert job.completed_at is not None


def test_worker_returns_none_when_queue_is_empty(tmp_path):
    repository = JobRepository(tmp_path / "jobs.db")
    service = JobService(repository)
    queue = JobQueue()

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=lambda job_id: ("synthetic.csv", "report.json"),
    )

    assert worker.run_once() is None