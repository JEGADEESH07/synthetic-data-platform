from fastapi.testclient import TestClient

from synthetic_data.api.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_version_endpoint():
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert "version" in response.json()


def test_unknown_endpoint_returns_404():
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404