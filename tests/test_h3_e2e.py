from pathlib import Path
import time

from fastapi.testclient import TestClient

from synthetic_data.api.app import app

from synthetic_data.api.metrics import Metrics
from synthetic_data.jobs.artifacts import ArtifactManager
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.background import BackgroundWorker
from synthetic_data.worker.engine import V02Engine
from synthetic_data.worker.executor import JobExecutionAdapter
from synthetic_data.worker.runtime import Worker
import synthetic_data.api.app as app_module


def wait_for_job_completion(
    client: TestClient,
    job_id: str,
    timeout_seconds: float = 120.0,
):
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        response = client.get(
            f"/api/v1/jobs/{job_id}",
        )

        assert response.status_code == 200

        body = response.json()

        if body["status"] in {"SUCCEEDED", "FAILED"}:
            return body

        time.sleep(0.25)

    raise AssertionError(
        f"Job {job_id} did not complete within "
        f"{timeout_seconds} seconds."
    )


def test_h3_end_to_end_job_execution(tmp_path, monkeypatch):
    input_file = Path("data/input/dev_dataset.csv")

    assert input_file.is_file()


    output_root = tmp_path / "jobs"
    output_root.mkdir()

    repository = JobRepository(output_root / "jobs.db")
    service = JobService(repository)
    queue = JobQueue()
    metrics = Metrics()
    engine = V02Engine(output_root=output_root)
    adapter = JobExecutionAdapter(job_service=service, engine=engine)
    worker = Worker(
        job_queue=queue,
        job_service=service,
        executor=adapter.execute,
        metrics=metrics,
    )
    background_worker = BackgroundWorker(worker=worker)

    monkeypatch.setattr(app_module, "job_repository", repository)
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)
    monkeypatch.setattr(app_module, "metrics", metrics)
    monkeypatch.setattr(app_module, "engine", engine)
    monkeypatch.setattr(app_module, "execution_adapter", adapter)
    monkeypatch.setattr(app_module, "worker", worker)
    monkeypatch.setattr(app_module, "background_worker", background_worker)
    monkeypatch.setattr(
        app_module,
        "artifact_manager",
        ArtifactManager(output_root),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs",
            json={
                "input_file": str(input_file),
                "row_count": 10,
            },
            headers={
                "X-Request-ID": "h3-e2e-request",
            },
        )

        assert response.status_code == 201

        body = response.json()

        assert "job_id" in body
        assert body["status"] == "QUEUED"

        job_id = body["job_id"]

        assert response.headers["X-Request-ID"] == (
            "h3-e2e-request"
        )

        final_job = wait_for_job_completion(
            client,
            job_id,
        )

        assert final_job["status"] == "SUCCEEDED"

        # H4: verify execution metadata is exposed through the API.
        execution_metadata = final_job["execution_metadata"]

        assert execution_metadata is not None
        assert execution_metadata["engine_version"] == "0.2.0"
        assert execution_metadata["seed"] == 42
        assert execution_metadata["ctgan_epochs"] == 10
        assert execution_metadata["requested_row_count"] == 10
        assert execution_metadata["generated_row_count"] == 10

        assert execution_metadata["source_schema_fingerprint"]
        assert execution_metadata["source_dataset_fingerprint"]
        assert execution_metadata["synthetic_schema_fingerprint"]
        assert execution_metadata["synthetic_dataset_fingerprint"]

        assert final_job["progress"] == 100
        assert final_job["execution_stage"] == "COMPLETED"

        assert final_job["started_at"] is not None
        assert final_job["completed_at"] is not None
        assert final_job["duration_seconds"] is not None

        assert final_job["synthetic_data_path"] is not None
        assert final_job["report_path"] is not None

        artifacts_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts",
        )

        assert artifacts_response.status_code == 200

        artifacts = artifacts_response.json()

        assert artifacts["job_id"] == job_id
        assert "synthetic_data.csv" in artifacts["artifacts"]
        assert "report.json" in artifacts["artifacts"]

        synthetic_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/synthetic_data.csv",
        )

        assert synthetic_response.status_code == 200
        assert synthetic_response.content

        report_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/report.json",
        )

        assert report_response.status_code == 200
        assert report_response.content

        # H4: verify the downloaded report contains audit evidence.
        report = report_response.json()
        audit = report["audit"]

        assert audit["engine"]["engine_version"] == "0.2.0"
        assert audit["reproducibility"]["seed"] == 42
        assert audit["reproducibility"]["ctgan_epochs"] == 10

        assert audit["environment"]["python_version"]
        assert audit["configuration"]["generation"]["seed"] == 42

        assert audit["dataset"]["source_schema_fingerprint"]
        assert audit["dataset"]["source_dataset_fingerprint"]
        assert audit["dataset"]["synthetic_schema_fingerprint"]
        assert audit["dataset"]["synthetic_dataset_fingerprint"]

        assert audit["execution"]["requested_row_count"] == 10
        assert audit["execution"]["generated_row_count"] == 10
