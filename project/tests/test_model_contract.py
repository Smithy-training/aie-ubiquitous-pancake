import math

import pytest

from app.core.config import get_settings
from app.models.schemas import PredictRequest
from app.services.model_loader import (
    EXPECTED_FEATURES,
    EXPECTED_MODEL_TYPE,
    EXPECTED_TARGET,
    PricingModelService,
)


@pytest.fixture(scope="module")
def model_service() -> PricingModelService:
    settings = get_settings()
    service = PricingModelService(
        model_path=settings.resolve_path(settings.ml.model_path),
        scaler_path=settings.resolve_path(settings.ml.scaler_path),
        metadata_path=settings.resolve_path(settings.ml.metadata_path),
        model_version=settings.ml.model_version,
    )
    service.load()
    return service


def assert_prediction_is_valid(result) -> None:
    assert isinstance(result.predicted_demand_units, int)
    assert result.predicted_demand_units > 0
    assert math.isfinite(result.recommended_price)
    assert result.recommended_price > 0
    assert math.isfinite(result.confidence_score)
    assert 0 <= result.confidence_score <= 1


def test_pretrained_model_metadata_contract(model_service: PricingModelService) -> None:
    metadata = model_service.metadata

    assert metadata["model_version"] == "v1"
    assert metadata["model_type"] == EXPECTED_MODEL_TYPE
    assert metadata["features"] == EXPECTED_FEATURES
    assert metadata["target"] == EXPECTED_TARGET
    assert metadata["dataset_version"] == "synthetic-pricing-v1-seed-42"
    assert metadata["training_rows"] == 1000
    assert metadata["metrics"]["mae"] <= 3.0
    assert metadata["metrics"]["rmse"] <= 4.0


def test_model_smoke_prediction_without_fastapi(model_service: PricingModelService) -> None:
    result = model_service.predict(
        PredictRequest(
            product_id="ELEC-100500",
            horizon_days=3,
            current_base_price=1500.0,
            is_weekend=True,
        )
    )

    assert_prediction_is_valid(result)
    assert 40 <= result.predicted_demand_units <= 50
    assert 1500 <= result.recommended_price <= 1650
    assert 0.7 <= result.confidence_score <= 0.95


@pytest.mark.parametrize(
    ("payload", "demand_range", "price_range", "confidence_range"),
    [
        (
            PredictRequest(
                product_id="ELEC-100500",
                horizon_days=1,
                current_base_price=1500.0,
                is_weekend=False,
            ),
            (38, 48),
            (1500, 1620),
            (0.7, 0.95),
        ),
        (
            PredictRequest(
                product_id="ELEC-100500",
                horizon_days=14,
                current_base_price=1500.0,
                is_weekend=False,
            ),
            (20, 35),
            (1400, 1520),
            (0.6, 0.85),
        ),
        (
            PredictRequest(
                product_id="HOME-001200",
                horizon_days=7,
                current_base_price=750.0,
                is_weekend=False,
            ),
            (38, 52),
            (730, 830),
            (0.5, 0.75),
        ),
        (
            PredictRequest(
                product_id="BOOK-777000",
                horizon_days=7,
                current_base_price=2800.0,
                is_weekend=True,
            ),
            (10, 25),
            (2500, 2850),
            (0.5, 0.75),
        ),
    ],
)
def test_model_edge_cases(
    model_service: PricingModelService,
    payload: PredictRequest,
    demand_range: tuple[int, int],
    price_range: tuple[float, float],
    confidence_range: tuple[float, float],
) -> None:
    result = model_service.predict(payload)

    assert_prediction_is_valid(result)
    assert demand_range[0] <= result.predicted_demand_units <= demand_range[1]
    assert price_range[0] <= result.recommended_price <= price_range[1]
    assert confidence_range[0] <= result.confidence_score <= confidence_range[1]


def test_model_handles_unknown_product_id(model_service: PricingModelService) -> None:
    result = model_service.predict(
        PredictRequest(
            product_id="UNKNOWN-000",
            horizon_days=3,
            current_base_price=1500.0,
            is_weekend=False,
        )
    )

    assert_prediction_is_valid(result)
    assert 25 <= result.predicted_demand_units <= 50
    assert 1450 <= result.recommended_price <= 1600


def test_model_low_confidence_scenario(model_service: PricingModelService) -> None:
    result = model_service.predict(
        PredictRequest(
            product_id="ELEC-100500",
            horizon_days=14,
            current_base_price=100000.0,
            is_weekend=False,
        )
    )

    assert_prediction_is_valid(result)
    assert result.confidence_score < 0.6
