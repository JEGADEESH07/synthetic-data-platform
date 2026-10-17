import json

from fastapi.testclient import TestClient

from synthetic_data.api.app import app
from synthetic_data.jobs.artifacts import ArtifactManager


client = TestClient(app)


def test_list_job_artifacts(tmp_path, monkeypatch):
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
            "input_file": "data/input/dev_dataset.csv",
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


def test_dashboard_summary_counts_successful_jobs_and_reports(
    tmp_path, monkeypatch
):
    from synthetic_data.api import app as app_module
    from synthetic_data.jobs.artifacts import ArtifactManager
    from synthetic_data.jobs.repository import JobRepository
    from synthetic_data.jobs.service import JobService
    from synthetic_data.jobs.models import JobStatus

    # Isolate this test from the existing project database.
    repository = JobRepository(str(tmp_path / "test_jobs.db"))
    service = JobService(repository)

    monkeypatch.setattr(app_module, "job_repository", repository)
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path / "artifacts"),
    )

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )
    assert job_response.status_code == 201

    job_id = job_response.json()["job_id"]
    job = service.get_job(job_id)
    assert job is not None

    job.status = JobStatus.SUCCEEDED
    repository.update(job)

    job_dir = tmp_path / "artifacts" / job_id
    job_dir.mkdir(parents=True)

    (job_dir / "report.json").write_text(
        json.dumps(
            {
                "schema_validation": {"valid": True},
                "statistical_quality": {
                    "overall_score": 0.95,
                    "minimum_score": 0.80,
                    "passed_columns": ["Age"],
                    "failed_columns": [],
                    "columns": [],
                },
                "privacy": {"status": "PASS"},
            }
        ),
        encoding="utf-8",
    )

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "datasets_generated": 1,
        "quality_evaluations": 1,
        "privacy_assessments": 1,
    }


def test_dashboard_summary_skips_missing_reports(tmp_path, monkeypatch):
    from synthetic_data.api import app as app_module
    from synthetic_data.jobs.artifacts import ArtifactManager
    from synthetic_data.jobs.repository import JobRepository
    from synthetic_data.jobs.service import JobService
    from synthetic_data.jobs.models import JobStatus

    repository = JobRepository(str(tmp_path / "missing_report_jobs.db"))
    service = JobService(repository)

    monkeypatch.setattr(app_module, "job_repository", repository)
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path / "artifacts"),
    )

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )
    assert job_response.status_code == 201

    job = service.get_job(job_response.json()["job_id"])
    assert job is not None

    job.status = JobStatus.SUCCEEDED
    repository.update(job)

    # Intentionally do not create report.json.
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "datasets_generated": 1,
        "quality_evaluations": 0,
        "privacy_assessments": 0,
    }


def test_dashboard_summary_does_not_count_schema_as_quality(
    tmp_path, monkeypatch
):
    from synthetic_data.api import app as app_module
    from synthetic_data.jobs.artifacts import ArtifactManager
    from synthetic_data.jobs.repository import JobRepository
    from synthetic_data.jobs.service import JobService
    from synthetic_data.jobs.models import JobStatus

    repository = JobRepository(str(tmp_path / "schema_only_jobs.db"))
    service = JobService(repository)

    monkeypatch.setattr(app_module, "job_repository", repository)
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(
        "synthetic_data.api.app.artifact_manager",
        ArtifactManager(tmp_path / "artifacts"),
    )

    job_response = client.post(
        "/api/v1/jobs",
        json={
            "input_file": "data/input/dev_dataset.csv",
            "row_count": 100,
        },
    )
    assert job_response.status_code == 201

    job = service.get_job(job_response.json()["job_id"])
    assert job is not None

    job.status = JobStatus.SUCCEEDED
    repository.update(job)

    job_dir = tmp_path / "artifacts" / job.job_id
    job_dir.mkdir(parents=True)

    (job_dir / "report.json").write_text(
        json.dumps(
            {
                "schema_validation": {"valid": True},
                "privacy": {"status": "PASS"},
            }
        ),
        encoding="utf-8",
    )

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "datasets_generated": 1,
        "quality_evaluations": 0,
        "privacy_assessments": 1,
    }
