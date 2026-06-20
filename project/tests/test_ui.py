from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI Pricing Service" in response.text
    assert "/v1/predict" in response.text
    assert "/v1/explain" in response.text
    assert "/v1/predictions/recent" in response.text
    assert "/v1/model/info" in response.text
    assert "RandomForestRegressor" in response.text
