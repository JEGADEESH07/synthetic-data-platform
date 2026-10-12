from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_readiness_endpoint():
    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }


def test_health_and_readiness_have_request_ids():
    health_response = client.get("/api/v1/health")
    readiness_response = client.get("/api/v1/readiness")

    assert health_response.headers["X-Request-ID"]
    assert readiness_response.headers["X-Request-ID"]


def test_readiness_preserves_request_id():
    request_id = "readiness-test-123"

    response = client.get(
        "/api/v1/readiness",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id