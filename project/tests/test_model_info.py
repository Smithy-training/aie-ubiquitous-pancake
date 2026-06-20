from fastapi.testclient import TestClient

from app.main import app
from app.services.model_loader import EXPECTED_FEATURES, EXPECTED_MODEL_TYPE, EXPECTED_TARGET


def test_version_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/version")

    body = response.json()
    assert response.status_code == 200
    assert body["service_name"] == "ai-pricing-service"
    assert body["service_version"] == "1.0.0"
    assert body["api_version"] == "v1"
    assert body["model_loaded"] is True
    assert body["model_version"] == "v1"
    assert body["model_type"] == EXPECTED_MODEL_TYPE
    assert body["dataset_version"] == "synthetic-pricing-v1-seed-42"


def test_model_info_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/v1/model/info")

    body = response.json()
    assert response.status_code == 200
    assert body["model_loaded"] is True
    assert body["model_version"] == "v1"
    assert body["contract_features"] == EXPECTED_FEATURES
    assert body["contract_target"] == EXPECTED_TARGET
    assert body["metadata"]["model_type"] == EXPECTED_MODEL_TYPE
    assert body["metadata"]["target"] == EXPECTED_TARGET
