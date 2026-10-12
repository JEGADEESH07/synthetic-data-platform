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
    assert body["status"] == "QUEUED"
    assert body["input_file"] == "data/input/dev_dataset.csv"
    assert body["row_count"] == 1000
    assert body["created_at"] is not None
    assert body["execution_stage"] == "QUEUED"
    assert body["progress"] == 0
    assert body["completed_units"] is None
    assert body["total_units"] is None
    assert body["duration_seconds"] is None


def test_get_unknown_job_returns_404():
    response = client.get(
        "/api/v1/jobs/does-not-exist",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error_code"] == "JOB_NOT_FOUND"
    assert body["message"] == "Job not found."
    assert body["request_id"] == response.headers["X-Request-ID"]

def test_request_id_is_generated_when_not_supplied():
    response = client.get(
        "/api/v1/version",
    )

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) > 0
    assert response.json()["version"]

def test_supplied_request_id_is_preserved():
    request_id = "test-request-123"

    response = client.get(
        "/api/v1/version",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id

def test_validation_error_contains_request_id():
    request_id = "validation-test-123"

    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/does-not-exist.csv",
            "row_count": 1000,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error_code"] == "JOB_VALIDATION_ERROR"
    assert body["request_id"] == request_id
    assert response.headers["X-Request-ID"] == request_id