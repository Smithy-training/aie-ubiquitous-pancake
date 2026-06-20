from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint() -> None:
    with TestClient(app) as client:
        client.post(
            "/v1/predict",
            json={
                "product_id": "ELEC-100500",
                "horizon_days": 3,
                "current_base_price": 1500.0,
                "is_weekend": True,
            },
        )
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "prediction_latency_seconds" in response.text
    assert "prediction_confidence_score" in response.text
    assert "model_prediction_confidence" in response.text
    assert "low_confidence_predictions_total" in response.text
    assert "model_errors_total" in response.text
