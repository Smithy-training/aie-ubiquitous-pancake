import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.metrics import (
    LOW_CONFIDENCE_PREDICTIONS_TOTAL,
    MODEL_ERRORS_TOTAL,
    MODEL_PREDICTION_CONFIDENCE,
    PREDICTION_CONFIDENCE_SCORE,
    PREDICTION_LATENCY_SECONDS,
)
from app.models.schemas import (
    BatchPredictItemResponse,
    BatchPredictRequest,
    BatchPredictResponse,
    ExplainResponse,
    ExplanationItem,
    PredictionHistoryItem,
    PredictionHistoryResponse,
    PredictRequest,
    PredictResponse,
)

router = APIRouter(prefix="/v1", tags=["prediction"])
logger = get_logger(__name__)


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    request_id = request.state.request_id
    response = _run_prediction(payload=payload, request=request, request_id=request_id)
    logger.info(
        "prediction_succeeded",
        request_id=request_id,
        product_id=payload.product_id,
        confidence_score=response.confidence_score,
    )
    return response


@router.post("/batch-predict", response_model=BatchPredictResponse)
def batch_predict(payload: BatchPredictRequest, request: Request) -> BatchPredictResponse:
    request_id = request.state.request_id
    items = [
        BatchPredictItemResponse(
            item_id=index,
            **_run_prediction(payload=item, request=request, request_id=request_id).model_dump(),
        )
        for index, item in enumerate(payload.items)
    ]

    logger.info("batch_prediction_succeeded", request_id=request_id, item_count=len(items))
    return BatchPredictResponse(request_id=request_id, status="success", items=items)


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: PredictRequest, request: Request) -> ExplainResponse:
    request_id = request.state.request_id
    prediction = _run_prediction(payload=payload, request=request, request_id=request_id)

    return ExplainResponse(
        request_id=request_id,
        prediction=prediction,
        explanations=_build_explanations(payload, request),
        model_note=(
            "The RandomForestRegressor predicts demand units. Recommended price is derived by service "
            "business logic from the demand forecast."
        ),
    )


@router.get("/predictions/recent", response_model=PredictionHistoryResponse)
def recent_predictions(request: Request) -> PredictionHistoryResponse:
    history = list(getattr(request.app.state, "prediction_history", []))
    return PredictionHistoryResponse(items=list(reversed(history)))


def _run_prediction(payload: PredictRequest, request: Request, request_id: str) -> PredictResponse:
    settings = get_settings()
    start_time = time.perf_counter()
    try:
        result = request.app.state.model_service.predict(payload)
    except Exception:
        MODEL_ERRORS_TOTAL.labels(error_type="inference").inc()
        logger.exception("prediction_failed", request_id=request_id, product_id=payload.product_id)
        raise

    latency = time.perf_counter() - start_time
    PREDICTION_LATENCY_SECONDS.observe(latency)
    MODEL_PREDICTION_CONFIDENCE.set(result.confidence_score)
    PREDICTION_CONFIDENCE_SCORE.observe(result.confidence_score)

    warning = None
    if result.confidence_score < settings.ml.min_confidence_threshold:
        warning = "Prediction confidence is below configured threshold"
        LOW_CONFIDENCE_PREDICTIONS_TOTAL.inc()

    response = PredictResponse(
        request_id=request_id,
        product_id=payload.product_id,
        predicted_demand_units=result.predicted_demand_units,
        recommended_price=result.recommended_price,
        confidence_score=result.confidence_score,
        status="success",
        warning=warning,
    )
    _append_history(request, payload, response)

    return response


def _append_history(request: Request, payload: PredictRequest, response: PredictResponse) -> None:
    history = getattr(request.app.state, "prediction_history", None)
    if history is None:
        return

    history.append(
        PredictionHistoryItem(
            request_id=response.request_id,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            current_base_price=payload.current_base_price,
            is_weekend=payload.is_weekend,
            predicted_demand_units=response.predicted_demand_units,
            recommended_price=response.recommended_price,
            confidence_score=response.confidence_score,
            warning=response.warning,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )


def _build_explanations(payload: PredictRequest, request: Request) -> list[ExplanationItem]:
    model_service = request.app.state.model_service
    scaler = model_service.scaler
    metadata = model_service.metadata
    price_min = float(scaler.get("price_min", 0.0))
    price_max = float(scaler.get("price_max", float("inf")))
    price_reference = float(scaler.get("price_reference", 1500.0))
    training_products = _known_products(model_service)

    explanations = [
        ExplanationItem(
            feature="product_id",
            effect="neutral" if payload.product_id in training_products else "negative",
            message=(
                "Product was present in the synthetic training data."
                if payload.product_id in training_products
                else "Product was not seen during training; categorical encoding falls back to unknown behavior."
            ),
        ),
        ExplanationItem(
            feature="horizon_days",
            effect="negative" if payload.horizon_days > 7 else "neutral",
            message=(
                "Longer forecast horizons usually reduce confidence."
                if payload.horizon_days > 7
                else "Forecast horizon is within the shorter, more stable range."
            ),
        ),
        ExplanationItem(
            feature="current_base_price",
            effect=_price_effect(payload.current_base_price, price_reference),
            message=(
                f"Training price range is approximately {price_min:.2f}..{price_max:.2f}; "
                f"reference price is {price_reference:.2f}."
            ),
        ),
        ExplanationItem(
            feature="is_weekend",
            effect="positive" if payload.is_weekend else "neutral",
            message=(
                "Weekend flag may increase expected demand in the synthetic training pattern."
                if payload.is_weekend
                else "Weekday request uses the baseline demand pattern."
            ),
        ),
        ExplanationItem(
            feature="model",
            effect="neutral",
            message=(
                f"Model {metadata.get('model_version')} uses {metadata.get('model_type')} "
                f"trained on {metadata.get('dataset_version')}."
            ),
        ),
    ]
    return explanations


def _price_effect(price: float, reference: float) -> str:
    if price < reference * 0.9:
        return "positive"
    if price > reference * 1.1:
        return "negative"
    return "neutral"


def _known_products(model_service) -> set[str]:
    estimator = model_service.model.get("estimator")
    vectorizer = getattr(estimator, "named_steps", {}).get("vectorizer") if estimator else None
    feature_names = vectorizer.get_feature_names_out() if vectorizer else []
    prefix = "product_id="
    return {name.removeprefix(prefix) for name in feature_names if name.startswith(prefix)}
