from synthetic_data.jobs.models import JobStatus
from synthetic_data.jobs.service import JobService


class FakeRepository:
    def __init__(self):
        self.jobs = {}

    def create(self, job):
        self.jobs[job.job_id] = job

    def get(self, job_id):
        return self.jobs.get(job_id)

    def update(self, job):
        self.jobs[job.job_id] = job


def test_job_lifecycle_transitions():
    repository = FakeRepository()
    service = JobService(repository)

    job = service.create_job(
        job_id="lifecycle-test",
        input_file="data/input/dev_dataset.csv",
        row_count=100,
    )

    assert job.status == JobStatus.CREATED

    service.queue_job(job.job_id)

    job = service.get_job(job.job_id)
    assert job.status == JobStatus.QUEUED

    service.mark_running(job.job_id)

    job = service.get_job(job.job_id)
    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None

    service.mark_succeeded(
        job.job_id,
        "data/output/jobs/lifecycle/synthetic_data.csv",
        "data/output/jobs/lifecycle/report.json",
    )

    job = service.get_job(job.job_id)

    assert job.status == JobStatus.SUCCEEDED
    assert job.completed_at is not None
    assert job.synthetic_data_path is not None
    assert job.report_path is not None


def test_job_lifecycle_failure():
    repository = FakeRepository()
    service = JobService(repository)

    job = service.create_job(
        job_id="lifecycle-failure-test",
        input_file="data/input/dev_dataset.csv",
        row_count=100,
    )

    service.queue_job(job.job_id)
    service.mark_running(job.job_id)

    service.mark_failed(
        job.job_id,
        error_code="JOB_EXECUTION_FAILED",
        error_message="Simulated engine failure",
    )

    job = service.get_job(job.job_id)

    assert job.status == JobStatus.FAILED
    assert job.completed_at is not None
    assert job.error_code == "JOB_EXECUTION_FAILED"
    assert job.error_message == "Simulated engine failure"

def test_worker_completes_full_success_lifecycle():
    from synthetic_data.jobs.service import JobService
    from synthetic_data.queue.job_queue import JobQueue
    from synthetic_data.worker.runtime import Worker

    repository = FakeRepository()
    service = JobService(repository)

    job = service.create_job(
        job_id="full-success-lifecycle",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    assert job.status == JobStatus.CREATED

    service.queue_job(job.job_id)

    queue = JobQueue()
    queue.enqueue(job.job_id)

    def fake_executor(job_id):
        current_job = service.get_job(job_id)

        assert current_job.status == JobStatus.RUNNING

        return (
            "data/output/jobs/test/synthetic_data.csv",
            "data/output/jobs/test/report.json",
        )

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=fake_executor,
    )

    processed_job_id = worker.run_once()

    assert processed_job_id == job.job_id

    final_job = service.get_job(job.job_id)

    assert final_job.status == JobStatus.SUCCEEDED
    assert final_job.started_at is not None
    assert final_job.completed_at is not None
    assert final_job.synthetic_data_path is not None
    assert final_job.report_path is not None

def test_worker_completes_full_failure_lifecycle():
    from synthetic_data.jobs.service import JobService
    from synthetic_data.queue.job_queue import JobQueue
    from synthetic_data.worker.runtime import Worker

    repository = FakeRepository()
    service = JobService(repository)

    job = service.create_job(
        job_id="full-failure-lifecycle",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    assert job.status == JobStatus.CREATED

    service.queue_job(job.job_id)

    queue = JobQueue()
    queue.enqueue(job.job_id)

    def failing_executor(job_id):
        current_job = service.get_job(job_id)

        assert current_job.status == JobStatus.RUNNING

        raise RuntimeError("Simulated execution failure")

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=failing_executor,
    )

    processed_job_id = worker.run_once()

    assert processed_job_id == job.job_id

    final_job = service.get_job(job.job_id)

    assert final_job.status == JobStatus.FAILED
    assert final_job.started_at is not None
    assert final_job.completed_at is not None
    assert final_job.error_code == "JOB_EXECUTION_FAILED"