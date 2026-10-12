from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from synthetic_data.api import app as app_module


def test_path_like_filename_cannot_escape_upload_directory():
    client = TestClient(app_module.app)

    csv_content = (
        "employee_id,name\n"
        "1,Alice\n"
        "2,Bob\n"
    )

    malicious_filenames = [
        "../outside.csv",
        "..\\outside.csv",
        "../../outside.csv",
        "nested/evil.csv",
        "nested\\evil.csv",
        "/tmp/evil.csv",
    ]

    for filename in malicious_filenames:
        response = client.post(
            "/api/v1/jobs/upload",
            files={
                "file": (
                    filename,
                    BytesIO(csv_content.encode("utf-8")),
                    "text/csv",
                )
            },
            data={"row_count": "10"},
        )

        assert response.status_code == 201

        job_id = response.json()["job_id"]
        job = app_module.job_service.get_job(job_id)

        assert job is not None

        input_path = Path(job.input_file)

        assert input_path.exists()
        assert input_path.is_file()
        assert input_path.parent.name == "uploads"

        # The client-controlled filename must never become
        # the server-side storage filename.
        assert input_path.name != Path(filename).name
        assert input_path.name.endswith(".csv")

        # The generated file must remain inside the upload directory.
        upload_root = Path("data/input/uploads").resolve()
        assert input_path.resolve().is_relative_to(upload_root)


def test_filename_does_not_control_storage_identity():
    client = TestClient(app_module.app)

    csv_content = (
        "id,name\n"
        "1,Alice\n"
    )

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "customer_data.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
        data={"row_count": "10"},
    )

    assert response.status_code == 201

    job_id = response.json()["job_id"]
    job = app_module.job_service.get_job(job_id)

    assert job is not None

    input_path = Path(job.input_file)

    assert input_path.exists()
    assert input_path.name != "customer_data.csv"
    assert input_path.name.endswith(".csv")

def test_invalid_csv_upload_is_rejected():
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "invalid.csv",
                BytesIO(b"\xff\xfe\xfd\xfc"),
                "text/csv",
            )
        },
        data={"row_count": "10"},
    )

    assert response.status_code == 400
    body = response.json()

    assert body["error_code"] == "JOB_VALIDATION_ERROR"
    assert "encoding" in body["message"].lower()


def test_unsupported_file_type_is_rejected():
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "dataset.txt",
                BytesIO(b"hello"),
                "text/plain",
            )
        },
        data={"row_count": "10"},
    )

    assert response.status_code == 400
    body = response.json()

    assert body["error_code"] == "JOB_VALIDATION_ERROR"
    assert "csv" in body["message"].lower()


def test_invalid_upload_does_not_create_job():
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "broken.csv",
                BytesIO(b"\xff\xfe\xfd"),
                "text/csv",
            )
        },
        data={"row_count": "10"},
    )

    assert response.status_code == 400