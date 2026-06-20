import time
from collections import deque
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api.health import router as health_router
from app.api.predict import router as predict_compat_router
from app.api.ui import router as ui_router
from app.api.v1.model import router as model_router
from app.api.v1.predict import router as predict_router
from app.api.version import router as version_router
from app.core.config import get_settings
from app.core.errors import ServiceError
from app.core.logger import configure_logging, get_logger
from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL, MODEL_ERRORS_TOTAL, render_metrics
from app.models.schemas import ErrorResponse
from app.services.model_loader import PricingModelService

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    model_service = PricingModelService(
        model_path=settings.resolve_path(settings.ml.model_path),
        scaler_path=settings.resolve_path(settings.ml.scaler_path),
        metadata_path=settings.resolve_path(settings.ml.metadata_path),
        model_version=settings.ml.model_version,
    )
    app.state.model_service = model_service
    app.state.prediction_history = deque(maxlen=50)

    logger.info(
        "service_starting",
        service=settings.app.name,
        service_version=settings.app.version,
        env=settings.app.env,
    )

    try:
        model_service.load()
        logger.info(
            "model_loaded",
            model_version=settings.ml.model_version,
            model_path=str(model_service.model_path),
        )
    except Exception as exc:
        MODEL_ERRORS_TOTAL.labels(error_type="load").inc()
        logger.error(
            "model_load_failed",
            error=str(exc),
            model_path=str(model_service.model_path),
            scaler_path=str(model_service.scaler_path),
            metadata_path=str(model_service.metadata_path),
        )

    yield

    logger.info("service_stopped", service=settings.app.name)


settings = get_settings()
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    started_at = time.perf_counter()

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)
    duration = time.perf_counter() - started_at
    endpoint = request.url.path
    status_code = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(endpoint=endpoint, status=status_code).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        endpoint=endpoint,
        method=request.method,
        status=status_code,
    ).observe(duration)

    logger.info(
        "http_request_completed",
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 3),
        client_ip=request.client.host if request.client else None,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    MODEL_ERRORS_TOTAL.labels(error_type=exc.code).inc()
    logger.error("service_error", request_id=request_id, code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            request_id=request_id,
            code=exc.code,
            message=exc.message,
        ).__dict__,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    endpoint = request.url.path
    logger.warning("validation_failed", request_id=request_id, endpoint=endpoint, errors=exc.errors())

    from fastapi.exception_handlers import request_validation_exception_handler

    return await request_validation_exception_handler(request, exc)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


app.include_router(health_router)
app.include_router(predict_compat_router)
app.include_router(predict_router)
app.include_router(model_router)
app.include_router(version_router)
app.include_router(ui_router)
