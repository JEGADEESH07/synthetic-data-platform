import time

from synthetic_data.jobs.models import JobStatus
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.background import BackgroundWorker
from synthetic_data.worker.runtime import Worker


class FakeRepository:
    def __init__(self):
        self.jobs = {}

    def create(self, job):
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id):
        return self.jobs.get(job_id)

    def update(self, job):
        self.jobs[job.job_id] = job
        return job


def wait_for_status(service, job_id, expected_status, timeout=5):
    start = time.time()

    while time.time() - start < timeout:
        job = service.get_job(job_id)

        if job is not None and job.status == expected_status:
            return job

        time.sleep(0.05)

    raise TimeoutError(
        f"Job {job_id} did not reach {expected_status}"
    )


def test_background_worker_executes_job(tmp_path):
    repository = FakeRepository()
    service = JobService(repository)
    queue = JobQueue()

    job = service.create_job(
        job_id="background-success",
        input_file="data/input/dev_dataset.csv",
        row_count=10,
    )

    service.queue_job(job.job_id)
    queue.enqueue(job.job_id)

    def executor(job_id):
        output_dir = tmp_path / "data" / "output" / "jobs" / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        synthetic_data_path = output_dir / "synthetic_data.csv"
        report_path = output_dir / "report.json"

        synthetic_data_path.write_text(
            "id,name\n1,test\n",
            encoding="utf-8",
        )
        report_path.write_text(
            "{}",
            encoding="utf-8",
        )

        return (
            str(synthetic_data_path),
            str(report_path),
        )

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=executor,
    )

    background_worker = BackgroundWorker(
        worker=worker,
        poll_interval=0.01,
    )

    background_worker.start()

    try:
        completed_job = wait_for_status(
            service,
            job.job_id,
            JobStatus.SUCCEEDED,
        )

        assert completed_job.synthetic_data_path is not None
        assert completed_job.report_path is not None

    finally:
        background_worker.stop()


def test_background_worker_stops_cleanly():
    repository = FakeRepository()
    service = JobService(repository)
    queue = JobQueue()

    def executor(job_id):
        return ("synthetic.csv", "report.json")

    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=executor,
    )

    background_worker = BackgroundWorker(
        worker=worker,
        poll_interval=0.01,
    )

    background_worker.start()
    background_worker.stop()

    assert background_worker._thread is None