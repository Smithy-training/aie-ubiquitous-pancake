from fastapi.testclient import TestClient

from app.main import app


def test_predict_success() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 3,
        "current_base_price": 1500.0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/predict", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["request_id"]
    assert body["product_id"] == payload["product_id"]
    assert body["predicted_demand_units"] > 0
    assert body["recommended_price"] > 0
    assert 0 <= body["confidence_score"] <= 1
    assert body["status"] == "success"
    assert "X-Request-ID" in response.headers


def test_unversioned_predict_compat_success() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 3,
        "current_base_price": 1500.0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["product_id"] == payload["product_id"]


def test_predict_uses_incoming_request_id() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 3,
        "current_base_price": 1500.0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/predict", json=payload, headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"
    assert response.json()["request_id"] == "test-request-id"


def test_predict_returns_warning_for_low_confidence() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 14,
        "current_base_price": 100000.0,
        "is_weekend": False,
    }

    with TestClient(app) as client:
        response = client.post("/v1/predict", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["confidence_score"] < 0.6
    assert body["warning"] == "Prediction confidence is below configured threshold"


def test_batch_predict_success() -> None:
    payload = {
        "items": [
            {
                "product_id": "ELEC-100500",
                "horizon_days": 3,
                "current_base_price": 1500.0,
                "is_weekend": True,
            },
            {
                "product_id": "BOOK-777000",
                "horizon_days": 7,
                "current_base_price": 2800.0,
                "is_weekend": True,
            },
        ]
    }

    with TestClient(app) as client:
        response = client.post("/v1/batch-predict", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["request_id"]
    assert body["status"] == "success"
    assert len(body["items"]) == 2
    assert body["items"][0]["item_id"] == 0
    assert body["items"][1]["item_id"] == 1
    assert body["items"][0]["predicted_demand_units"] > 0


def test_explain_success() -> None:
    payload = {
        "product_id": "UNKNOWN-000",
        "horizon_days": 14,
        "current_base_price": 100000.0,
        "is_weekend": False,
    }

    with TestClient(app) as client:
        response = client.post("/v1/explain", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["prediction"]["product_id"] == payload["product_id"]
    assert body["prediction"]["confidence_score"] < 0.6
    assert body["model_note"]
    assert {item["feature"] for item in body["explanations"]} >= {
        "product_id",
        "horizon_days",
        "current_base_price",
        "is_weekend",
        "model",
    }


def test_recent_predictions_contains_prediction() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 3,
        "current_base_price": 1500.0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        predict_response = client.post("/v1/predict", json=payload)
        history_response = client.get("/v1/predictions/recent")

    history = history_response.json()["items"]
    assert predict_response.status_code == 200
    assert history_response.status_code == 200
    assert history
    assert history[0]["request_id"] == predict_response.json()["request_id"]


def test_predict_rejects_invalid_horizon_days() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 15,
        "current_base_price": 1500.0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/predict", json=payload)

    assert response.status_code == 422


def test_predict_rejects_invalid_current_base_price() -> None:
    payload = {
        "product_id": "ELEC-100500",
        "horizon_days": 3,
        "current_base_price": 0,
        "is_weekend": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/predict", json=payload)

    assert response.status_code == 422
