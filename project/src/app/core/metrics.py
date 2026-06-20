from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the service.",
    ["endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["endpoint", "method", "status"],
)

PREDICTION_LATENCY_SECONDS = Histogram(
    "prediction_latency_seconds",
    "Prediction request latency in seconds.",
)

PREDICTION_CONFIDENCE_SCORE = Histogram(
    "prediction_confidence_score",
    "Prediction confidence score distribution.",
    buckets=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0),
)

MODEL_PREDICTION_CONFIDENCE = Gauge(
    "model_prediction_confidence",
    "Latest model prediction confidence score.",
)

LOW_CONFIDENCE_PREDICTIONS_TOTAL = Counter(
    "low_confidence_predictions_total",
    "Predictions with confidence below configured threshold.",
)

MODEL_ERRORS_TOTAL = Counter(
    "model_errors_total",
    "Model loading and inference errors.",
    ["error_type"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
