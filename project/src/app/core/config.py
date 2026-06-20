import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "configs" / "config.yaml").is_file() and (candidate / "artifacts").is_dir():
            return candidate
    raise RuntimeError("Project root with configs/ and artifacts/ was not found")


PROJECT_ROOT = _find_project_root()


class AppConfig(BaseModel):
    name: str = "ai-pricing-service"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "production"


class ApiConfig(BaseModel):
    version: str = "v1"


class MlConfig(BaseModel):
    model_path: str = "./artifacts/model_v1.pkl"
    scaler_path: str = "./artifacts/scaler_v1.pkl"
    metadata_path: str = "./artifacts/model_metadata.json"
    model_version: str = "v1"
    min_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    api: ApiConfig = ApiConfig()
    ml: MlConfig = MlConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    def resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return PROJECT_ROOT / candidate


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")

    return data


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    for key, value in os.environ.items():
        parts = key.lower().split("__", maxsplit=1)
        if len(parts) != 2:
            continue

        section, field = parts
        if section not in {"app", "api", "ml"}:
            continue

        data.setdefault(section, {})[field] = value

    return data


@lru_cache
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    config_path = PROJECT_ROOT / "configs" / "config.yaml"
    data = _apply_env_overrides(_read_yaml(config_path))
    return Settings(**data)
