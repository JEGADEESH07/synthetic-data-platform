import pytest
from fastapi.testclient import TestClient

from synthetic_data.api.app import app, job_queue


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_job_queue():
    while job_queue.dequeue() is not None:
        pass

    yield

    while job_queue.dequeue() is not None:
        pass


def test_create_job_queues_job():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"]
    assert data["status"] == "QUEUED"


def test_created_job_is_present_in_queue():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )

    assert response.status_code == 201

    job_id = response.json()["job_id"]

    queued_job_id = job_queue.dequeue()

    assert queued_job_id == job_id