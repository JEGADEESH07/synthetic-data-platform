import time

from fastapi.testclient import TestClient

from synthetic_data.api.app import app, job_queue

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


def wait_for_job_completion(client, job_id, timeout=60):
    start = time.time()

    while time.time() - start < timeout:
        response = client.get(f"/api/v1/jobs/{job_id}")

        assert response.status_code == 200

        status = response.json()["status"]

        if status in {"SUCCEEDED", "FAILED"}:
            return response.json()

        time.sleep(0.5)

    raise TimeoutError(
        f"Job {job_id} did not finish within {timeout} seconds"
    )



def test_api_to_engine_end_to_end(tmp_path, monkeypatch):
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
                "input_file": "data/input/dev_dataset.csv",
                "row_count": 10,
            },
        )

        assert response.status_code == 201
        body = response.json()
        job_id = body["job_id"]

        assert job_id
        assert body["status"] == "QUEUED"

        result = wait_for_job_completion(client, job_id)

        assert result["status"] == "SUCCEEDED"
        assert result["job_id"] == job_id
        assert result["synthetic_data_path"] is not None
        assert result["report_path"] is not None
        assert result["completed_at"] is not None

        artifacts_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts"
        )
        assert artifacts_response.status_code == 200

        artifacts_body = artifacts_response.json()
        assert artifacts_body["job_id"] == job_id
        assert "synthetic_data.csv" in artifacts_body["artifacts"]
        assert "report.json" in artifacts_body["artifacts"]

        csv_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/synthetic_data.csv"
        )
        assert csv_response.status_code == 200
        assert len(csv_response.content) > 0

        report_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/report.json"
        )
        assert report_response.status_code == 200
        assert len(report_response.content) > 0
