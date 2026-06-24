"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """The health endpoint should return success and status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "ok"
    assert payload["data"]["status"] == "ok"
    assert payload["error"] is None
