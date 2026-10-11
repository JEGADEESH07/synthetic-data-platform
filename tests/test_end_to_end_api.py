import time

from fastapi.testclient import TestClient

from synthetic_data.api.app import app, job_queue


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


def test_api_to_engine_end_to_end():
    with TestClient(app) as client:
        # 1. Create job
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

        # 2. Wait for execution
        result = wait_for_job_completion(client, job_id)

        assert result["status"] == "SUCCEEDED"

        # 3. Verify persisted job result
        assert result["job_id"] == job_id
        assert result["synthetic_data_path"] is not None
        assert result["report_path"] is not None
        assert result["completed_at"] is not None

        # 4. Verify artifact listing
        artifacts_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts"
        )

        assert artifacts_response.status_code == 200

        artifacts_body = artifacts_response.json()

        assert artifacts_body["job_id"] == job_id
        assert "synthetic_data.csv" in artifacts_body["artifacts"]
        assert "report.json" in artifacts_body["artifacts"]

        # 5. Verify synthetic CSV download
        csv_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/synthetic_data.csv"
        )

        assert csv_response.status_code == 200
        assert len(csv_response.content) > 0

        # 6. Verify report JSON download
        report_response = client.get(
            f"/api/v1/jobs/{job_id}/artifacts/report.json"
        )

        assert report_response.status_code == 200
        assert len(report_response.content) > 0