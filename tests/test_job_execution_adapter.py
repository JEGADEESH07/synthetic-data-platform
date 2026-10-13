
import json
from pathlib import Path

import pytest

from synthetic_data.jobs.models import Job, JobStatus
from synthetic_data.worker.executor import JobExecutionAdapter


class FakeJobService:
    def __init__(self, job):
        self.job = job
        self.saved_metadata = None

    def get_job(self, job_id):
        if job_id == self.job.job_id:
            return self.job
        return None

    def set_execution_metadata(self, job_id, execution_metadata):
        assert job_id == self.job.job_id
        self.saved_metadata = execution_metadata
        self.job.execution_metadata = execution_metadata
        return self.job


class FakeEngine:
    def __init__(self, report_path):
        self.report_path = report_path
        self.calls = []

    def execute(self, job_id, input_file, row_count):
        self.calls.append((job_id, input_file, row_count))

        return type(
            "Artifacts",
            (),
            {
                "synthetic_data_path": Path(
                    "data/output/jobs/test/synthetic_data.csv"
                ),
                "report_path": self.report_path,
            },
        )()


@pytest.fixture
def audit_report(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "audit": {
                    "engine": {"engine_version": "0.2.0"},
                    "reproducibility": {
                        "seed": 42,
                        "ctgan_epochs": 10,
                    },
                    "execution": {
                        "requested_row_count": 100,
                        "generated_row_count": 100,
                    },
                    "dataset": {
                        "source_schema_fingerprint": "source-schema",
                        "source_dataset_fingerprint": "source-data",
                        "synthetic_schema_fingerprint": "synthetic-schema",
                        "synthetic_dataset_fingerprint": "synthetic-data",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return report_path


def make_job():
    return Job(
        job_id="job-123",
        input_file="data/input/dev_dataset.csv",
        row_count=100,
        status=JobStatus.RUNNING,
    )


def test_execution_adapter_passes_job_and_persists_audit(
    audit_report,
):
    job = make_job()
    job_service = FakeJobService(job)
    engine = FakeEngine(audit_report)
    adapter = JobExecutionAdapter(job_service, engine)

    result = adapter.execute("job-123")

    assert engine.calls == [
        ("job-123", "data/input/dev_dataset.csv", 100)
    ]
    assert result == (
        str(Path("data/output/jobs/test/synthetic_data.csv")),
        str(audit_report),
    )
    assert job_service.saved_metadata == {
        "engine_version": "0.2.0",
        "seed": 42,
        "ctgan_epochs": 10,
        "requested_row_count": 100,
        "generated_row_count": 100,
        "source_schema_fingerprint": "source-schema",
        "source_dataset_fingerprint": "source-data",
        "synthetic_schema_fingerprint": "synthetic-schema",
        "synthetic_dataset_fingerprint": "synthetic-data",
    }


def test_execution_adapter_rejects_unknown_job(tmp_path):
    job = make_job()
    adapter = JobExecutionAdapter(
        FakeJobService(job),
        FakeEngine(tmp_path / "unused.json"),
    )

    with pytest.raises(ValueError, match="Job not found: unknown-job"):
        adapter.execute("unknown-job")


def test_execution_adapter_rejects_missing_audit_metadata(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    job = make_job()
    job_service = FakeJobService(job)
    adapter = JobExecutionAdapter(
        job_service,
        FakeEngine(report_path),
    )

    with pytest.raises(RuntimeError, match="Audit metadata missing"):
        adapter.execute(job.job_id)

    assert job_service.saved_metadata is None
