import logging

import pytest

from synthetic_data.api.metrics import Metrics
from synthetic_data.jobs.models import JobStatus
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.runtime import Worker


class ListHandler(logging.Handler):
    """Capture log records locally for worker observability tests."""

    def __init__(self):
        super().__init__(level=logging.NOTSET)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture(autouse=True)
def reset_worker_logger():
    logger = logging.getLogger("synthetic_data.worker")

    original_level = logger.level
    original_propagate = logger.propagate
    original_handlers = list(logger.handlers)

    yield

    logger.setLevel(original_level)
    logger.propagate = original_propagate

    logger.handlers.clear()
    logger.handlers.extend(original_handlers)


def create_worker(tmp_path, executor):
    repository = JobRepository(
        tmp_path / "jobs.db"
    )
    service = JobService(repository)
    queue = JobQueue()
    metrics = Metrics()

    job_id = "observability-job"

    service.create_job(
        job_id=job_id,
        input_file="data/input/dev_dataset.csv",
        row_count=100,
    )

    service.queue_job(job_id)
    queue.enqueue(job_id)

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=executor,
        metrics=metrics,
    )

    return worker, service, metrics, job_id


def test_worker_logs_success(tmp_path):
    def executor(job_id):
        synthetic = tmp_path / "synthetic_data.csv"
        report = tmp_path / "report.json"

        synthetic.write_text(
            "id,name\n1,Alice\n",
            encoding="utf-8",
        )

        report.write_text(
            '{"status":"PASS"}',
            encoding="utf-8",
        )

        return str(synthetic), str(report)

    worker, service, metrics, job_id = create_worker(
        tmp_path,
        executor,
    )

    worker_logger = logging.getLogger("synthetic_data.worker")
    handler = ListHandler()
    worker_logger.addHandler(handler)

    try:
        worker_logger.setLevel(logging.INFO)

        result = worker.run_once()

        assert result == job_id

        job = service.get_job(job_id)

        assert job is not None
        assert job.status == JobStatus.SUCCEEDED

        messages = [
            record.getMessage()
            for record in handler.records
        ]

        assert any(
            "Worker picked up job" in message
            and job_id in message
            for message in messages
        )

        assert any(
            "Job execution started" in message
            and job_id in message
            for message in messages
        )

        assert any(
            "Job execution succeeded" in message
            and job_id in message
            for message in messages
        )

        snapshot = metrics.snapshot()

        assert snapshot.worker_executions_total == 1
        assert snapshot.jobs_succeeded_total == 1
        assert snapshot.jobs_failed_total == 0
        assert snapshot.worker_execution_duration_seconds >= 0

    finally:
        worker_logger.removeHandler(handler)


def test_worker_logs_failure(tmp_path):
    def executor(job_id):
        raise RuntimeError("synthetic generation failed")

    worker, service, metrics, job_id = create_worker(
        tmp_path,
        executor,
    )

    worker_logger = logging.getLogger("synthetic_data.worker")
    handler = ListHandler()
    worker_logger.addHandler(handler)

    try:
        worker_logger.setLevel(logging.INFO)

        result = worker.run_once()

        assert result == job_id

        job = service.get_job(job_id)

        assert job is not None
        assert job.status == JobStatus.FAILED
        assert job.error_code == "JOB_EXECUTION_FAILED"

        messages = [
            record.getMessage()
            for record in handler.records
        ]

        assert any(
            "Worker picked up job" in message
            and job_id in message
            for message in messages
        )

        assert any(
            "Job execution failed" in message
            and job_id in message
            and "JOB_EXECUTION_FAILED" in message
            for message in messages
        )

        assert any(
            "Job marked failed" in message
            and job_id in message
            and "JOB_EXECUTION_FAILED" in message
            for message in messages
        )

        snapshot = metrics.snapshot()

        assert snapshot.worker_executions_total == 1
        assert snapshot.jobs_succeeded_total == 0
        assert snapshot.jobs_failed_total == 1
        assert snapshot.worker_execution_duration_seconds >= 0

    finally:
        worker_logger.removeHandler(handler)