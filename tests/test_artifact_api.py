import json

from fastapi.testclient import TestClient

from synthetic_data.api.app import app
from synthetic_data.jobs.artifacts import ArtifactManager


client = TestClient(app)


def test_list_job_artifacts(tmp_path, monkeypatch):
    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/customer_data.csv",
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
        json.dumps({"status": "PASS"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path),
    )

    response = client.get(
        f"/api/v1/jobs/{job_id}/artifacts"
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id,
        "artifacts": [
            "synthetic_data.csv",
            "report.json",
        ],
    }


def test_get_job_artifact(tmp_path, monkeypatch):
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
        json.dumps({"status": "PASS"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path),
    )

    response = client.get(
        f"/api/v1/jobs/{job_id}/artifacts/report.json"
    )

    assert response.status_code == 200
    assert response.json() == {"status": "PASS"}


def test_unknown_artifact_returns_404():
    response = client.get(
        "/api/v1/jobs/does-not-exist/artifacts/report.json"
    )

    assert response.status_code == 404