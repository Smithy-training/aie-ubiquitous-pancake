from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.models.schemas import VersionResponse

router = APIRouter(tags=["version"])


@router.get("/version", response_model=VersionResponse)
def version(request: Request) -> VersionResponse:
    settings = get_settings()
    model_service = request.app.state.model_service
    metadata = model_service.metadata or {}

    return VersionResponse(
        service_name=settings.app.name,
        service_version=settings.app.version,
        api_version=settings.api.version,
        model_loaded=model_service.model_loaded,
        model_version=model_service.model_version,
        model_type=metadata.get("model_type"),
        dataset_version=metadata.get("dataset_version"),
    )
