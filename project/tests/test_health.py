from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service_version": "1.0.0",
        "api_version": "v1",
    }


def test_live() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["model_loaded"] is True
    assert body["model_version"] == "v1"
    assert body["metadata"]["model_version"] == "v1"
    assert body["metadata"]["dataset_version"] == "synthetic-pricing-v1-seed-42"
    assert "mae" in body["metadata"]["metrics"]


def test_ready_returns_503_when_model_is_not_loaded() -> None:
    with TestClient(app) as client:
        original_state = client.app.state.model_service.model_loaded
        client.app.state.model_service.model_loaded = False
        response = client.get("/health/ready")
        client.app.state.model_service.model_loaded = original_state

    body = response.json()
    assert response.status_code == 503
    assert body["code"] == "model_not_ready"
    assert body["request_id"]
