from pathlib import Path

from synthetic_data.jobs.models import Job
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.engine import V02Engine
from synthetic_data.worker.executor import JobExecutionAdapter
from synthetic_data.worker.runtime import Worker


class FakeRepository:
    def __init__(self):
        self.jobs = {}

    def create(self, job):
        self.jobs[job.job_id] = job

    def get(self, job_id):
        return self.jobs.get(job_id)

    def update(self, job):
        self.jobs[job.job_id] = job


def test_worker_executes_job_through_v02_engine(tmp_path):
    repository = FakeRepository()

    from synthetic_data.jobs.service import JobService

    job_service = JobService(repository)

    job = job_service.create_job(
        job_id="worker-engine-test",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    job_service.queue_job(job.job_id)

    queue = JobQueue()
    queue.enqueue(job.job_id)

    engine = V02Engine(output_root=tmp_path)

    adapter = JobExecutionAdapter(
        job_service=job_service,
        engine=engine,
    )

    worker = Worker(
        job_queue=queue,
        job_service=job_service,
        executor=adapter.execute,
    )

    processed_job_id = worker.run_once()

    assert processed_job_id == job.job_id

    completed_job = job_service.get_job(job.job_id)

    assert completed_job is not None
    assert completed_job.status.value == "SUCCEEDED"

    assert completed_job.synthetic_data_path is not None
    assert completed_job.report_path is not None

    assert Path(completed_job.synthetic_data_path).exists()
    assert Path(completed_job.report_path).exists()

def test_worker_marks_job_failed_when_engine_fails():
    from synthetic_data.jobs.service import JobService

    class FailingEngine:
        def execute(self, job_id, input_file, row_count):
            raise RuntimeError("simulated engine failure")

    repository = FakeRepository()
    job_service = JobService(repository)

    job = job_service.create_job(
        job_id="worker-engine-failure-test",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    job_service.queue_job(job.job_id)

    queue = JobQueue()
    queue.enqueue(job.job_id)

    adapter = JobExecutionAdapter(
        job_service=job_service,
        engine=FailingEngine(),
    )

    worker = Worker(
        job_queue=queue,
        job_service=job_service,
        executor=adapter.execute,
    )

    processed_job_id = worker.run_once()

    assert processed_job_id == job.job_id

    failed_job = job_service.get_job(job.job_id)

    assert failed_job is not None
    assert failed_job.status.value == "FAILED"
    assert failed_job.error_code == "JOB_EXECUTION_FAILED"