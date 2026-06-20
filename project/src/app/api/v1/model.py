from fastapi import APIRouter, Request

from app.core.errors import ModelNotReadyError
from app.models.schemas import ModelInfoResponse
from app.services.model_loader import EXPECTED_FEATURES, EXPECTED_TARGET

router = APIRouter(prefix="/v1/model", tags=["model"])


@router.get("/info", response_model=ModelInfoResponse)
def model_info(request: Request) -> ModelInfoResponse:
    model_service = request.app.state.model_service
    if not model_service.model_loaded:
        raise ModelNotReadyError()

    return ModelInfoResponse(
        model_loaded=True,
        model_version=model_service.model_version,
        contract_features=EXPECTED_FEATURES,
        contract_target=EXPECTED_TARGET,
        metadata=model_service.metadata,
    )
