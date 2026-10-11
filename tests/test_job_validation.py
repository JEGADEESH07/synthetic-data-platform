from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_missing_input_file_is_rejected():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "",
            "row_count": 100,
        },
    )

    assert response.status_code == 422


def test_zero_row_count_is_rejected():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 0,
        },
    )

    assert response.status_code == 422


def test_negative_row_count_is_rejected():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": -10,
        },
    )

    assert response.status_code == 422


def test_non_csv_file_is_rejected():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/customer_data.txt",
            "row_count": 100,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "JOB_VALIDATION_ERROR",
        "message": "Input file must be a CSV file.",
    }


def test_missing_input_file_path_is_rejected():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/does_not_exist.csv",
            "row_count": 100,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "JOB_VALIDATION_ERROR",
        "message": "Input file does not exist.",
    }


def test_valid_input_is_accepted():
    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["job_id"]
    assert body["status"] == "QUEUED"