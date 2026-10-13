from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_unknown_job_returns_structured_error():
    request_id = "error-test-job"

    response = client.get(
        "/api/v1/jobs/does-not-exist",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "JOB_NOT_FOUND",
        "message": "Job not found.",
        "request_id": request_id,
    }

    assert response.headers["X-Request-ID"] == request_id


def test_unknown_job_artifact_returns_structured_error():
    request_id = "error-test-artifact"

    response = client.get(
        "/api/v1/jobs/does-not-exist/artifacts/report.json",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "JOB_NOT_FOUND",
        "message": "Job not found.",
        "request_id": request_id,
    }

    assert response.headers["X-Request-ID"] == request_id


def test_unknown_artifact_name_returns_structured_error(
    tmp_path,
    monkeypatch,
):
    from synthetic_data.jobs.artifacts import ArtifactManager

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )

    assert job_response.status_code == 201

    job_id = job_response.json()["job_id"]

    job_dir = tmp_path / job_id
    job_dir.mkdir()

    (job_dir / "synthetic_data.csv").write_text(
        "id,name\n1,Alice\n",
        encoding="utf-8",
    )

    (job_dir / "report.json").write_text(
        '{"status":"PASS"}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path),
    )

    request_id = "error-test-unknown-artifact"

    response = client.get(
        f"/api/v1/jobs/{job_id}/artifacts/private.txt",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "ARTIFACT_NOT_FOUND",
        "message": "Artifact not found.",
        "request_id": request_id,
    }

    assert response.headers["X-Request-ID"] == request_id


def test_schema_validation_returns_consistent_error():
    request_id = "error-test-validation"

    response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "",
            "row_count": 1000,
        },
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 422

    assert response.json() == {
        "error_code": "REQUEST_VALIDATION_ERROR",
        "message": "Request validation failed.",
        "request_id": request_id,
    }

    assert response.headers["X-Request-ID"] == request_id



def test_error_does_not_expose_internal_details():
    response = client.get(
        "/api/v1/jobs/does-not-exist",
    )

    body = response.json()
    response_text = response.text.lower()

    assert "traceback" not in body
    assert "exception" not in body
    assert "stack" not in body

    assert "traceback" not in response_text
    assert "runtimeerror" not in response_text
    assert "file not found" not in response_text
    assert "c:\\users\\" not in response_text
    assert "/home/" not in response_text
