import json
import shutil

import pytest

from app.core.config import get_settings
from app.core.errors import ModelLoadError
from app.services.model_loader import PricingModelService


def test_model_loader_rejects_checksum_mismatch(tmp_path) -> None:
    settings = get_settings()
    model_path = tmp_path / "model_v1.pkl"
    scaler_path = tmp_path / "scaler_v1.pkl"
    metadata_path = tmp_path / "model_metadata.json"

    shutil.copyfile(settings.resolve_path(settings.ml.model_path), model_path)
    shutil.copyfile(settings.resolve_path(settings.ml.scaler_path), scaler_path)
    shutil.copyfile(settings.resolve_path(settings.ml.metadata_path), metadata_path)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["artifacts"]["model_sha256"] = "bad-checksum"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    service = PricingModelService(
        model_path=model_path,
        scaler_path=scaler_path,
        metadata_path=metadata_path,
        model_version=settings.ml.model_version,
    )

    with pytest.raises(ModelLoadError):
        service.load()


def test_model_loader_rejects_metadata_contract_mismatch(tmp_path) -> None:
    settings = get_settings()
    model_path = tmp_path / "model_v1.pkl"
    scaler_path = tmp_path / "scaler_v1.pkl"
    metadata_path = tmp_path / "model_metadata.json"

    shutil.copyfile(settings.resolve_path(settings.ml.model_path), model_path)
    shutil.copyfile(settings.resolve_path(settings.ml.scaler_path), scaler_path)
    shutil.copyfile(settings.resolve_path(settings.ml.metadata_path), metadata_path)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["features"] = ["unexpected_feature"]
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    service = PricingModelService(
        model_path=model_path,
        scaler_path=scaler_path,
        metadata_path=metadata_path,
        model_version=settings.ml.model_version,
    )

    with pytest.raises(ModelLoadError):
        service.load()
