from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import main
from app.jobs.store import JobStore
from app.storage.artifacts import ArtifactStore

@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """
    Create an API client using isolated temporary storage.
    """

    database_path = tmp_path / "jobs.db"
    artifacts_path = tmp_path / "jobs"

    monkeypatch.setattr(
        main,
        "job_store",
        JobStore(str(database_path)),
    )

    monkeypatch.setattr(
        main,
        "artifact_store",
        ArtifactStore(str(artifacts_path)),
    )

    return TestClient(main.app)


def test_health_check(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_readiness_check(api_client):
    response = api_client.get("/readiness")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready"
    }


def test_generate_rejects_invalid_rows(api_client):
    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 1_000_001,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nSYN1,25\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

def test_generate_creates_completed_job(
    api_client,
    monkeypatch,
):
    """
    Verify the complete API job lifecycle for
    a successful generation.
    """

    def fake_generate(
        self,
        input_path,
        output_rows,
        epochs,
        output_data_path=None,
        output_report_path=None,
    ):
        return {
            "saved_files": {
                "synthetic_data": output_data_path,
                "evaluation_report": output_report_path,
            },
            "evaluation": {
                "schema": {
                    "valid": True,
                },
                "privacy": {
                    "safe": True,
                },
                "trust": {
                    "trust_score": 0.85,
                },
                "quality_gate": {
                    "passed": True,
                    "trust_score": 0.85,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [],
                },
            },
        }

    monkeypatch.setattr(
        main.SyntheticDataService,
        "generate",
        fake_generate,
    )

    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 100,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nC1,25\nC2,30\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    created = response.json()

    assert "job_id" in created

    job_id = created["job_id"]

    status_response = api_client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert status_response.status_code == 200

    job = status_response.json()

    assert job["job_id"] == job_id
    assert job["status"] == "completed"
    assert job["error"] is None

    assert len(job["attempts"]) == 1
    assert job["attempts"][0]["attempt_number"] == 1
    assert job["attempts"][0]["status"] == "completed"

    assert job["selected_attempt"] is not None
    assert (
        job["selected_attempt"]["attempt_number"]
        == 1
    )

    assert (
        job["result"]["quality_gate"]["passed"]
        is True
    )

def test_generate_regenerates_until_quality_passes(
    api_client,
    monkeypatch,
):
    """
    Verify that a failed quality gate triggers
    regeneration and that a later passing attempt
    completes the job.
    """

    results = [
        {
            "saved_files": {},
            "evaluation": {
                "schema": {
                    "valid": True,
                },
                "privacy": {
                    "safe": True,
                },
                "trust": {
                    "trust_score": 0.65,
                },
                "quality_gate": {
                    "passed": False,
                    "trust_score": 0.65,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [
                        "Trust score is below the minimum required threshold."
                    ],
                },
            },
        },
        {
            "saved_files": {},
            "evaluation": {
                "schema": {
                    "valid": True,
                },
                "privacy": {
                    "safe": True,
                },
                "trust": {
                    "trust_score": 0.82,
                },
                "quality_gate": {
                    "passed": True,
                    "trust_score": 0.82,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [],
                },
            },
        },
    ]

    call_count = 0

    def fake_generate(
        self,
        input_path,
        output_rows,
        epochs,
        output_data_path=None,
        output_report_path=None,
    ):
        nonlocal call_count

        result = results[call_count]
        call_count += 1

        return result

    monkeypatch.setattr(
        main.SyntheticDataService,
        "generate",
        fake_generate,
    )

    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 100,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nC1,25\nC2,30\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    job_id = response.json()["job_id"]

    status_response = api_client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert status_response.status_code == 200

    job = status_response.json()

    assert job["status"] == "completed"

    assert len(job["attempts"]) == 2

    assert (
        job["attempts"][0]["status"]
        == "quality_failed"
    )

    assert (
        job["attempts"][1]["status"]
        == "completed"
    )

    assert job["selected_attempt"] is not None

    assert (
        job["selected_attempt"]["attempt_number"]
        == 2
    )

    assert (
        job["selected_attempt"]["trust_score"]
        == 0.82
    )

    assert (
        job["result"]["regeneration"]["attempts_used"]
        == 2
    )

    assert (
        job["result"]["regeneration"]["regenerated"]
        is True
    )

    assert (
        job["result"]["regeneration"]["stopping_reason"]
        == "quality_gate_passed"
    )

    assert call_count == 2

def test_generate_fails_after_max_regeneration_attempts(
    api_client,
    monkeypatch,
):
    """
    Verify that a job fails after all allowed
    regeneration attempts fail the quality gate.
    """

    call_count = 0

    def fake_generate(
        self,
        input_path,
        output_rows,
        epochs,
        output_data_path=None,
        output_report_path=None,
    ):
        nonlocal call_count
        call_count += 1

        return {
            "saved_files": {},
            "evaluation": {
                "schema": {
                    "valid": True,
                },
                "privacy": {
                    "safe": True,
                },
                "trust": {
                    "trust_score": 0.60,
                },
                "quality_gate": {
                    "passed": False,
                    "trust_score": 0.60,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [
                        "Trust score is below the minimum required threshold."
                    ],
                },
            },
        }

    monkeypatch.setattr(
        main.SyntheticDataService,
        "generate",
        fake_generate,
    )

    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 100,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nC1,25\nC2,30\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    job_id = response.json()["job_id"]

    status_response = api_client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert status_response.status_code == 200

    job = status_response.json()

    assert job["status"] == "failed"

    assert len(job["attempts"]) == 3

    assert all(
        attempt["status"] == "quality_failed"
        for attempt in job["attempts"]
    )

    assert all(
        attempt["trust_score"] == 0.60
        for attempt in job["attempts"]
    )

    assert job["selected_attempt"] is not None

    assert (
        job["selected_attempt"]["attempt_number"]
        == 1
    )

    assert (
        job["selected_attempt"]["trust_score"]
        == 0.60
    )

    assert (
        job["result"]["regeneration"]["attempts_used"]
        == 3
    )

    assert (
        job["result"]["regeneration"]["max_attempts"]
        == 3
    )

    assert (
        job["result"]["regeneration"]["regenerated"]
        is True
    )

    assert (
        job["result"]["regeneration"]["stopping_reason"]
        == "maximum_attempts_reached"
    )

    assert call_count == 3

def test_completed_job_artifacts_are_accessible(
    api_client,
    monkeypatch,
):
    """
    Verify that completed-job artifacts can be listed
    and downloaded through the API.
    """

    def fake_generate(
        self,
        input_path,
        output_rows,
        epochs,
        output_data_path=None,
        output_report_path=None,
    ):
        from pathlib import Path

        Path(output_data_path).write_text(
            "Customer_ID,Age\nSYN1,25\n"
        )

        Path(output_report_path).write_text(
            '{"schema":{"valid":true}}'
        )

        return {
            "saved_files": {
                "synthetic_data": output_data_path,
                "evaluation_report": output_report_path,
            },
            "evaluation": {
                "schema": {"valid": True},
                "privacy": {"safe": True},
                "trust": {"trust_score": 0.85},
                "quality_gate": {
                    "passed": True,
                    "trust_score": 0.85,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [],
                },
            },
        }

    monkeypatch.setattr(
        main.SyntheticDataService,
        "generate",
        fake_generate,
    )

    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 100,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nC1,25\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    job_id = response.json()["job_id"]

    artifacts_response = api_client.get(
        f"/api/v1/jobs/{job_id}/artifacts"
    )

    assert artifacts_response.status_code == 200

    artifacts = artifacts_response.json()

    assert artifacts["job_id"] == job_id
    assert artifacts["selected_attempt"] is not None

    assert "synthetic_data" in artifacts["artifacts"]
    assert "evaluation_report" in artifacts["artifacts"]

    synthetic_response = api_client.get(
        f"/api/v1/jobs/{job_id}/artifacts/synthetic_data"
    )

    assert synthetic_response.status_code == 200
    assert (
        "Customer_ID,Age"
        in synthetic_response.text
    )

    report_response = api_client.get(
        f"/api/v1/jobs/{job_id}/artifacts/evaluation_report"
    )

    assert report_response.status_code == 200
    assert (
        '"schema":{"valid":true}'
        in report_response.text
    )

def test_unknown_artifact_returns_404(
    api_client,
    monkeypatch,
):
    """
    Verify that an unknown artifact name returns 404.
    """

    def fake_generate(
        self,
        input_path,
        output_rows,
        epochs,
        output_data_path=None,
        output_report_path=None,
    ):
        from pathlib import Path

        Path(output_data_path).write_text(
            "Customer_ID,Age\nSYN1,25\n"
        )

        Path(output_report_path).write_text(
            '{"schema":{"valid":true}}'
        )

        return {
            "saved_files": {
                "synthetic_data": output_data_path,
                "evaluation_report": output_report_path,
            },
            "evaluation": {
                "schema": {"valid": True},
                "privacy": {"safe": True},
                "trust": {"trust_score": 0.85},
                "quality_gate": {
                    "passed": True,
                    "trust_score": 0.85,
                    "schema_valid": True,
                    "privacy_safe": True,
                    "reasons": [],
                },
            },
        }

    monkeypatch.setattr(
        main.SyntheticDataService,
        "generate",
        fake_generate,
    )

    response = api_client.post(
        "/api/v1/generate",
        data={
            "rows": 100,
            "epochs": 1,
        },
        files={
            "file": (
                "test.csv",
                b"Customer_ID,Age\nC1,25\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    job_id = response.json()["job_id"]

    artifact_response = api_client.get(
        f"/api/v1/jobs/{job_id}/artifacts/not_a_real_artifact"
    )

    assert artifact_response.status_code == 404

    assert (
        artifact_response.json()["detail"]
        == "Artifact 'not_a_real_artifact' was not found."
    )