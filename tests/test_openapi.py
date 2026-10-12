from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_openapi_document_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    assert document["info"]["title"] == (
        "Synthetic Data Engineering & Privacy Platform"
    )

    assert document["info"]["version"] == "0.3.0"


def test_openapi_contains_expected_api_routes():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected_paths = {
        "/api/v1/health",
        "/api/v1/readiness",
        "/api/v1/version",
        "/api/v1/jobs",
        "/api/v1/jobs/upload",
        "/api/v1/jobs/{job_id}",
        "/api/v1/jobs/{job_id}/artifacts",
        "/api/v1/jobs/{job_id}/artifacts/{artifact_name}",
    }

    assert expected_paths.issubset(paths.keys())


def test_openapi_documents_multipart_upload():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    upload_operation = document["paths"][
        "/api/v1/jobs/upload"
    ]["post"]

    request_body = upload_operation["requestBody"]

    assert "multipart/form-data" in request_body["content"]


def test_openapi_documents_job_schemas():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()

    schemas = document["components"]["schemas"]

    assert "JobCreateRequest" in schemas
    assert "JobCreateResponse" in schemas
    assert "JobStatusResponse" in schemas
    assert "ArtifactListResponse" in schemas