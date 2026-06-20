from fastapi import APIRouter, Request

from app.api.v1.predict import _run_prediction
from app.models.schemas import PredictRequest, PredictResponse

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictResponse)
def predict_compat(payload: PredictRequest, request: Request) -> PredictResponse:
    return _run_prediction(payload=payload, request=request, request_id=request.state.request_id)
