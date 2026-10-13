
import json
from pathlib import Path

from synthetic_data.jobs.repository import JobRepository
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
    repository = JobRepository(tmp_path / "jobs.db")

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

    # Verify audit metadata in the persisted report.
    report = json.loads(
        Path(completed_job.report_path).read_text(
            encoding="utf-8"
        )
    )

    assert isinstance(report["audit"], dict)
    assert report["audit"]["engine"]["engine_version"] == "0.2.0"
    assert report["audit"]["reproducibility"]["seed"] == 42
    assert report["audit"]["dataset"]["source_dataset_fingerprint"]

    # Verify execution metadata was recorded on the job.
    assert completed_job.execution_metadata is not None
    assert completed_job.execution_metadata["engine_version"] == "0.2.0"
    assert completed_job.execution_metadata["seed"] == 42
    assert completed_job.execution_metadata["generated_row_count"] == 10

    # Re-read the job from SQLite to verify metadata persistence.
    reloaded_job = job_service.get_job(job.job_id)

    assert reloaded_job is not None
    assert reloaded_job.execution_metadata == completed_job.execution_metadata



def test_worker_marks_job_failed_when_engine_fails(tmp_path):
    from synthetic_data.jobs.service import JobService

    class FailingEngine:
        def execute(self, job_id, input_file, row_count):
            raise RuntimeError("simulated engine failure")

    repository = JobRepository(tmp_path / "failure-jobs.db")
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
    assert failed_job.synthetic_data_path is None
    assert failed_job.report_path is None

    # The failure state must survive a read from SQLite.
    reloaded_job = job_service.get_job(job.job_id)

    assert reloaded_job is not None
    assert reloaded_job.status.value == "FAILED"
    assert reloaded_job.error_code == "JOB_EXECUTION_FAILED"
    assert reloaded_job.error_message is not None
