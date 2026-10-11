from pathlib import Path

from synthetic_data.jobs.models import Job
from synthetic_data.worker.executor import JobExecutionAdapter


class FakeJobService:
    def __init__(self, job):
        self.job = job

    def get_job(self, job_id):
        if job_id == self.job.job_id:
            return self.job
        return None


class FakeEngine:
    def __init__(self):
        self.calls = []

    def execute(self, job_id, input_file, row_count):
        self.calls.append((job_id, input_file, row_count))

        return type(
            "Artifacts",
            (),
            {
                "synthetic_data_path": Path("data/output/jobs/test/synthetic_data.csv"),
                "report_path": Path("data/output/jobs/test/report.json"),
            },
        )()


def test_execution_adapter_passes_job_to_engine():
    job = Job(
        job_id="job-123",
        input_file="data/input/dev_dataset.csv",
        row_count=100,
    )

    job_service = FakeJobService(job)
    engine = FakeEngine()

    adapter = JobExecutionAdapter(job_service, engine)

    result = adapter.execute("job-123")

    assert engine.calls == [
        ("job-123", "data/input/dev_dataset.csv", 100)
    ]

    assert result == (
        str(Path("data/output/jobs/test/synthetic_data.csv")),
        str(Path("data/output/jobs/test/report.json")),
    )


def test_execution_adapter_rejects_unknown_job():
    job = Job(
        job_id="job-123",
        input_file="data/input/dev_dataset.csv",
        row_count=100,
    )

    adapter = JobExecutionAdapter(
        FakeJobService(job),
        FakeEngine(),
    )

    try:
        adapter.execute("unknown-job")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Job not found: unknown-job"