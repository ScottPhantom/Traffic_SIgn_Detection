from fastapi.testclient import TestClient

from cpv301_autodrive.api import app


def test_health_reports_downloaded_model() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_exists"] is True
