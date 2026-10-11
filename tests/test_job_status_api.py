from fastapi.testclient import TestClient

from synthetic_data.api.app import app
from synthetic_data.api.app import job_service


client = TestClient(app)


def test_get_job_status():
    created = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 1000,
        },
    )

    assert created.status_code == 201

    job_id = created.json()["job_id"]

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200

    body = response.json()

    assert body["job_id"] == job_id
    assert body["status"] == "CREATED"
    assert body["input_file"] == "data/input/dev_dataset.csv"
    assert body["row_count"] == 1000
    assert body["created_at"] is not None


def test_get_unknown_job_returns_404():
    response = client.get(
        "/api/v1/jobs/does-not-exist",
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "JOB_NOT_FOUND",
        "message": "Job not found.",
    }