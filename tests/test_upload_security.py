from io import BytesIO
from pathlib import Path
import pytest
from fastapi import UploadFile
from synthetic_data.api.uploads import UploadValidationError, save_uploaded_csv
from synthetic_data.config.settings import InputConfig
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

def test_oversized_upload_is_rejected_and_temporary_file_is_removed(
    tmp_path,
):
    config = InputConfig(
        allowed_root=tmp_path / "input",
        max_file_size_mb=0,
        max_input_rows=100,
        max_output_rows=100,
        encoding="utf-8",
        allow_symlinks=False,
        reject_duplicate_columns=True,
    )

    upload = UploadFile(
        filename="oversized.csv",
        file=BytesIO(b"id,value\n1,100\n"),
    )

    with pytest.raises(
        UploadValidationError,
        match="maximum allowed size",
    ):
        save_uploaded_csv(upload, config)

    upload_directory = config.allowed_root / "uploads"

    assert list(upload_directory.iterdir()) == []


def test_api_rejects_oversized_upload_without_creating_job(
    monkeypatch,
    tmp_path,
):
    client = TestClient(app_module.app)

    config = InputConfig(
        allowed_root=tmp_path / "input",
        max_file_size_mb=0,
        max_input_rows=100,
        max_output_rows=100,
        encoding="utf-8",
        allow_symlinks=False,
        reject_duplicate_columns=True,
    )

    monkeypatch.setattr(
        app_module,
        "_get_input_config",
        lambda: config,
    )

    create_job_calls = []
    original_create_job = app_module.job_service.create_job


    def track_create_job(*args, **kwargs):
        create_job_calls.append(True)
        return original_create_job(*args, **kwargs)


    monkeypatch.setattr(
        app_module.job_service,
        "create_job",
        track_create_job,
    )

    response = client.post(
        "/api/v1/jobs/upload",
        files={
            "file": (
                "oversized.csv",
                BytesIO(b"id,value\n1,100\n"),
                "text/csv",
            )
        },
        data={"row_count": "10"},
    )

    assert response.status_code == 400
    assert "maximum allowed size" in response.json()["message"].lower()
    assert create_job_calls == []
    upload_directory = config.allowed_root / "uploads"
    assert list(upload_directory.iterdir()) == []
