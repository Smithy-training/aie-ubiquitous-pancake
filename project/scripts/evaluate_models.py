import argparse
import json
from pathlib import Path

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor
from train_model import as_feature_matrix, as_target, generate_dataset


def evaluate_models(seed: int = 42, rows: int = 1000) -> dict:
    data = generate_dataset(seed=seed, rows=rows)
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=seed)
    x_train = as_feature_matrix(train_data)
    y_train = as_target(train_data)
    x_test = as_feature_matrix(test_data)
    y_test = as_target(test_data)

    estimators = {
        "DummyRegressor": DummyRegressor(strategy="mean"),
        "LinearRegression": LinearRegression(),
        "DecisionTreeRegressor": DecisionTreeRegressor(
            max_depth=8,
            min_samples_leaf=3,
            random_state=seed,
        ),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=120,
            min_samples_leaf=3,
            random_state=seed,
            n_jobs=-1,
        ),
    }

    metrics = {}
    for name, estimator in estimators.items():
        pipeline = Pipeline(
            steps=[
                ("vectorizer", DictVectorizer(sparse=False)),
                ("regressor", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        metrics[name] = {
            "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
            "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 4),
        }

    return {
        "dataset": f"synthetic-pricing-v1-seed-{seed}",
        "rows": rows,
        "train_rows": len(train_data),
        "test_rows": len(test_data),
        "random_state": seed,
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate pricing model baselines.")
    parser.add_argument("--output", default="reports/model_comparison.json")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = evaluate_models(seed=args.seed, rows=args.rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
