from typing import Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    product_id: str = Field(..., min_length=1, examples=["ELEC-100500"])
    horizon_days: int = Field(..., ge=1, le=14, examples=[3])
    current_base_price: float = Field(..., gt=0, examples=[1500.0])
    is_weekend: bool = Field(default=False, examples=[True])


class PredictResponse(BaseModel):
    request_id: str
    product_id: str
    predicted_demand_units: int
    recommended_price: float
    confidence_score: float = Field(..., ge=0, le=1)
    status: Literal["success"]
    warning: str | None = None


class BatchPredictRequest(BaseModel):
    items: list[PredictRequest] = Field(..., min_length=1, max_length=50)


class BatchPredictItemResponse(PredictResponse):
    item_id: int


class BatchPredictResponse(BaseModel):
    request_id: str
    status: Literal["success"]
    items: list[BatchPredictItemResponse]


class ExplanationItem(BaseModel):
    feature: str
    effect: Literal["positive", "negative", "neutral"]
    message: str


class ExplainResponse(BaseModel):
    request_id: str
    prediction: PredictResponse
    explanations: list[ExplanationItem]
    model_note: str


class PredictionHistoryItem(BaseModel):
    request_id: str
    product_id: str
    horizon_days: int
    current_base_price: float
    is_weekend: bool
    predicted_demand_units: int
    recommended_price: float
    confidence_score: float
    warning: str | None = None
    created_at: str


class PredictionHistoryResponse(BaseModel):
    items: list[PredictionHistoryItem]


class ModelMetadata(BaseModel):
    model_version: str
    model_type: str
    trained_at: str
    dataset_version: str
    training_rows: int
    training_target_mean: float
    features: list[str]
    target: str
    metrics: dict[str, float]


class HealthResponse(BaseModel):
    status: str
    service_version: str
    api_version: str


class LiveResponse(BaseModel):
    status: Literal["alive"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    model_loaded: bool
    model_version: str
    metadata: ModelMetadata


class VersionResponse(BaseModel):
    service_name: str
    service_version: str
    api_version: str
    model_loaded: bool
    model_version: str
    model_type: str | None = None
    dataset_version: str | None = None


class ModelInfoResponse(BaseModel):
    model_loaded: bool
    model_version: str
    contract_features: list[str]
    contract_target: str
    metadata: ModelMetadata


class ErrorResponse(BaseModel):
    request_id: str
    code: str
    message: str
