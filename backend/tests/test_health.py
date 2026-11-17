from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Verify that root endpoint returns HTTP 200 and expected service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data
    assert "name" in data


def test_health_check_endpoint(client: TestClient) -> None:
    """Verify that the health check endpoint returns healthy status and metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
    assert "timestamp" in data
