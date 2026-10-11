from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_create_job():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 1000,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "job_id" in body
    assert body["status"] == "CREATED"


def test_create_job_requires_input_file():
    response = client.post(
        "/api/v1/jobs",
        json={
            "row_count": 1000,
        },
    )

    assert response.status_code == 422


def test_create_job_requires_positive_row_count():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 0,
        },
    )

    assert response.status_code == 422