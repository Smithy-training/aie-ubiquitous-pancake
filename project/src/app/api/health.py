from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.errors import ModelNotReadyError
from app.models.schemas import HealthResponse, LiveResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service_version=settings.app.version,
        api_version=settings.api.version,
    )


@router.get("/health/live", response_model=LiveResponse)
def live() -> LiveResponse:
    return LiveResponse(status="alive")


@router.get("/health/ready", response_model=ReadyResponse)
def ready(request: Request) -> ReadyResponse:
    model_service = request.app.state.model_service
    if not model_service.model_loaded:
        raise ModelNotReadyError()

    model_service.readiness_probe()

    return ReadyResponse(
        status="ready",
        model_loaded=True,
        model_version=model_service.model_version,
        metadata=model_service.metadata,
    )
