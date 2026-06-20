import argparse
import json
import pickle
import random
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

FEATURES = ["product_id", "horizon_days", "current_base_price", "is_weekend"]
TARGET = "demand_units"


def generate_dataset(seed: int, rows: int) -> list[dict[str, float | int | bool | str]]:
    rng = random.Random(seed)
    products = ["ELEC-100500", "ELEC-200100", "HOME-001200", "SPORT-420000", "BOOK-777000"]
    data = []

    for _ in range(rows):
        product_id = rng.choice(products)
        horizon_days = rng.randint(1, 14)
        current_base_price = round(rng.uniform(700, 2800), 2)
        is_weekend = rng.random() > 0.65

        category_factor = {
            "ELEC": 1.15,
            "HOME": 0.95,
            "SPORT": 1.05,
            "BOOK": 0.8,
        }[product_id.split("-", maxsplit=1)[0]]
        price_factor = max(0.5, min(1.4, 1500.0 / current_base_price))
        horizon_factor = max(0.58, 1.0 - ((horizon_days - 1) * 0.038))
        weekend_factor = 1.14 if is_weekend else 1.0
        noise = rng.uniform(-3.0, 3.0)
        demand = max(1, round(42.0 * category_factor * price_factor * horizon_factor * weekend_factor + noise))

        data.append(
            {
                "product_id": product_id,
                "horizon_days": horizon_days,
                "current_base_price": current_base_price,
                "is_weekend": is_weekend,
                "demand_units": demand,
            }
        )

    return data


def as_feature_matrix(data: list[dict[str, float | int | bool | str]]) -> list[dict[str, float | int | bool | str]]:
    return [{feature: row[feature] for feature in FEATURES} for row in data]


def as_target(data: list[dict[str, float | int | bool | str]]) -> np.ndarray:
    return np.array([float(row[TARGET]) for row in data])


def train_model(
    data: list[dict[str, float | int | bool | str]],
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, float]]:
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=seed)
    x_train = as_feature_matrix(train_data)
    y_train = as_target(train_data)
    x_test = as_feature_matrix(test_data)
    y_test = as_target(test_data)

    estimator = RandomForestRegressor(
        n_estimators=120,
        min_samples_leaf=3,
        random_state=seed,
        n_jobs=-1,
    )
    pipeline = Pipeline(
        steps=[
            ("vectorizer", DictVectorizer(sparse=False)),
            ("regressor", estimator),
        ]
    )
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 4),
    }

    price_values = [float(row["current_base_price"]) for row in train_data]
    scaler = {
        "version": "v1",
        "price_reference": round(float(np.mean(price_values)), 4),
        "price_min": round(float(np.min(price_values)), 4),
        "price_max": round(float(np.max(price_values)), 4),
    }
    model = {
        "version": "v1",
        "model_type": "random_forest_regressor",
        "estimator": pipeline,
        "features": FEATURES,
        "target": TARGET,
    }
    return model, scaler, metrics


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Train sklearn pricing model artifacts.")
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = generate_dataset(seed=args.seed, rows=args.rows)
    model, scaler, metrics = train_model(dataset, seed=args.seed)

    model_path = output_dir / "model_v1.pkl"
    scaler_path = output_dir / "scaler_v1.pkl"
    metadata_path = output_dir / "model_metadata.json"

    with model_path.open("wb") as file:
        pickle.dump(model, file)
    with scaler_path.open("wb") as file:
        pickle.dump(scaler, file)

    metadata = {
        "model_version": "v1",
        "model_type": model["model_type"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_version": f"synthetic-pricing-v1-seed-{args.seed}",
        "training_rows": args.rows,
        "training_target_mean": round(float(np.mean(as_target(dataset))), 4),
        "features": FEATURES,
        "target": TARGET,
        "metrics": metrics,
        "artifacts": {
            "model_path": str(model_path.as_posix()),
            "model_sha256": file_sha256(model_path),
            "scaler_path": str(scaler_path.as_posix()),
            "scaler_sha256": file_sha256(scaler_path),
        },
    }

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
