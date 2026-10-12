from pathlib import Path
import time

from fastapi.testclient import TestClient

from synthetic_data.api.app import app


def wait_for_job_completion(
    client: TestClient,
    job_id: str,
    timeout_seconds: float = 30.0,
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


def test_h3_end_to_end_job_execution():
    input_file = Path("data/input/dev_dataset.csv")

    assert input_file.is_file()

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