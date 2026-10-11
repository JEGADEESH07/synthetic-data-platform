from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_unknown_job_returns_structured_error():
    response = client.get(
        "/api/v1/jobs/does-not-exist"
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "JOB_NOT_FOUND",
        "message": "Job not found.",
    }


def test_unknown_job_artifact_returns_structured_error():
    response = client.get(
        "/api/v1/jobs/does-not-exist/artifacts/report.json"
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "JOB_NOT_FOUND",
        "message": "Job not found.",
    }


def test_unknown_artifact_name_returns_structured_error(tmp_path, monkeypatch):
    from synthetic_data.api.app import artifact_manager
    from synthetic_data.jobs.artifacts import ArtifactManager

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/customer_data.csv",
            "row_count": 100,
        },
    )

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

    response = client.get(
        f"/api/v1/jobs/{job_id}/artifacts/private.txt"
    )

    assert response.status_code == 404

    assert response.json() == {
        "error_code": "ARTIFACT_NOT_FOUND",
        "message": "Artifact not found.",
    }