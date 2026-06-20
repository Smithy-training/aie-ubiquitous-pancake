import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.core.errors import ModelLoadError, ModelNotReadyError
from app.models.schemas import PredictRequest

EXPECTED_FEATURES = ["product_id", "horizon_days", "current_base_price", "is_weekend"]
EXPECTED_MODEL_TYPE = "random_forest_regressor"
EXPECTED_TARGET = "demand_units"


@dataclass
class PredictionResult:
    predicted_demand_units: int
    recommended_price: float
    confidence_score: float


class PricingModelService:
    def __init__(self, model_path: Path, scaler_path: Path, metadata_path: Path, model_version: str) -> None:
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.metadata_path = metadata_path
        self.model_version = model_version
        self.model_loaded = False
        self.model: dict = {}
        self.scaler: dict = {}
        self.metadata: dict = {}
        self.load_error: str | None = None

    def load(self) -> None:
        try:
            with self.model_path.open("rb") as model_file:
                self.model = pickle.load(model_file)

            with self.scaler_path.open("rb") as scaler_file:
                self.scaler = pickle.load(scaler_file)

            with self.metadata_path.open("r", encoding="utf-8") as metadata_file:
                self.metadata = json.load(metadata_file)

            self._validate_metadata()
            self.readiness_probe()
        except Exception as exc:
            self.model_loaded = False
            self.load_error = str(exc)
            raise ModelLoadError(str(exc)) from exc

        self.load_error = None
        self.model_loaded = True

    def predict(self, payload: PredictRequest) -> PredictionResult:
        if not self.model_loaded:
            raise ModelNotReadyError()

        predicted_demand = self._predict_demand(payload)
        price_reference = float(self.scaler.get("price_reference", 1500.0))
        raw_price_factor = price_reference / payload.current_base_price

        predicted_demand_units = max(1, round(predicted_demand))
        base_demand = float(self.metadata.get("training_target_mean", 40.0))

        demand_pressure = max(-0.12, min(0.18, (predicted_demand_units - base_demand) / 250))
        recommended_price = round(payload.current_base_price * (1.0 + demand_pressure), 2)

        confidence_score = self._confidence_score(payload, predicted_demand, raw_price_factor)

        return PredictionResult(
            predicted_demand_units=predicted_demand_units,
            recommended_price=recommended_price,
            confidence_score=confidence_score,
        )

    def _predict_demand(self, payload: PredictRequest) -> float:
        estimator = self.model.get("estimator")
        if estimator is None:
            raise ModelLoadError("Model estimator is missing")

        row = [self._payload_to_features(payload)]
        return float(estimator.predict(row)[0])

    def _confidence_score(self, payload: PredictRequest, predicted_demand: float, raw_price_factor: float) -> float:
        estimator = self.model.get("estimator")
        regressor = getattr(estimator, "named_steps", {}).get("regressor") if estimator else None
        transformed = estimator.named_steps["vectorizer"].transform([self._payload_to_features(payload)])

        if hasattr(regressor, "estimators_"):
            tree_predictions = np.array([tree.predict(transformed)[0] for tree in regressor.estimators_])
            relative_std = float(np.std(tree_predictions) / max(abs(predicted_demand), 1.0))
        else:
            relative_std = 0.15

        price_min = float(self.scaler.get("price_min", 0.0))
        price_max = float(self.scaler.get("price_max", float("inf")))
        out_of_range_penalty = 0.0
        if payload.current_base_price < price_min or payload.current_base_price > price_max:
            out_of_range_penalty = 0.2

        score = 0.95 - relative_std - abs(1.0 - raw_price_factor) * 0.18 - payload.horizon_days * 0.008
        return round(max(0.5, min(0.95, score - out_of_range_penalty)), 2)

    @staticmethod
    def _payload_to_features(payload: PredictRequest) -> dict[str, Any]:
        return {
            "product_id": payload.product_id,
            "horizon_days": payload.horizon_days,
            "current_base_price": payload.current_base_price,
            "is_weekend": payload.is_weekend,
        }

    def readiness_probe(self) -> None:
        probe_payload = PredictRequest(
            product_id="READY-CHECK",
            horizon_days=1,
            current_base_price=1500.0,
            is_weekend=False,
        )
        result = self.predict_without_ready_check(probe_payload)
        if result.predicted_demand_units <= 0:
            raise ModelLoadError("Readiness probe returned invalid demand")

    def predict_without_ready_check(self, payload: PredictRequest) -> PredictionResult:
        model_loaded = self.model_loaded
        self.model_loaded = True
        try:
            return self.predict(payload)
        finally:
            self.model_loaded = model_loaded

    def _validate_metadata(self) -> None:
        metadata_version = self.metadata.get("model_version")
        model_version = self.model.get("version")
        scaler_version = self.scaler.get("version")
        version_mismatch = (
            metadata_version != self.model_version
            or model_version != self.model_version
            or scaler_version != self.model_version
        )
        if version_mismatch:
            raise ModelLoadError(
                f"Model version mismatch: config={self.model_version}, "
                f"metadata={metadata_version}, model={model_version}, scaler={scaler_version}"
            )

        if self.metadata.get("model_type") != EXPECTED_MODEL_TYPE:
            raise ModelLoadError(f"Unexpected model type: {self.metadata.get('model_type')}")

        if self.metadata.get("features") != EXPECTED_FEATURES:
            raise ModelLoadError(f"Unexpected feature contract: {self.metadata.get('features')}")

        if self.metadata.get("target") != EXPECTED_TARGET:
            raise ModelLoadError(f"Unexpected target: {self.metadata.get('target')}")

        if self.model.get("features") != EXPECTED_FEATURES:
            raise ModelLoadError(f"Unexpected model features: {self.model.get('features')}")

        if self.model.get("target") != EXPECTED_TARGET:
            raise ModelLoadError(f"Unexpected model target: {self.model.get('target')}")

        artifacts = self.metadata.get("artifacts", {})
        expected_model_sha = artifacts.get("model_sha256")
        expected_scaler_sha = artifacts.get("scaler_sha256")
        if expected_model_sha and self._file_sha256(self.model_path) != expected_model_sha:
            raise ModelLoadError("Model checksum mismatch")
        if expected_scaler_sha and self._file_sha256(self.scaler_path) != expected_scaler_sha:
            raise ModelLoadError("Scaler checksum mismatch")

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
