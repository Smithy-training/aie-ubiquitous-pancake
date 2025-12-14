from __future__ import annotations

import pandas as pd
import pytest

from eda_cli.core import (
    compute_quality_flags,
    correlation_matrix,
    flatten_summary_for_print,
    missing_table,
    summarize_dataset,
    top_categories,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [10, 20, 30, None],
            "height": [140, 150, 160, 170],
            "city": ["A", "B", "A", None],
        }
    )


def test_summarize_dataset_basic():
    df = _sample_df()
    summary = summarize_dataset(df)

    assert summary.n_rows == 4
    assert summary.n_cols == 3
    assert any(c.name == "age" for c in summary.columns)
    assert any(c.name == "city" for c in summary.columns)

    summary_df = flatten_summary_for_print(summary)
    assert "name" in summary_df.columns
    assert "missing_share" in summary_df.columns


def test_missing_table_and_quality_flags():
    df = _sample_df()
    missing_df = missing_table(df)

    assert "missing_count" in missing_df.columns
    assert missing_df.loc["age", "missing_count"] == 1

    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df, df)
    assert 0.0 <= flags["quality_score"] <= 1.0


def test_correlation_and_top_categories():
    df = _sample_df()
    corr = correlation_matrix(df)
    assert isinstance(corr, pd.DataFrame)

    top_cats = top_categories(df, max_columns=5, top_k=2)
    assert "city" in top_cats
    city_table = top_cats["city"]
    assert "value" in city_table.columns
    assert len(city_table) <= 2




def test_quality_flags_constant_column():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": ["A", "A", "A", "A"],
        "value": [10, 20, 30, 40]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_constant_columns"] is True
    assert "name" in [col.name for col in summary.columns if col.unique == 1]


def test_quality_flags_no_constant_column():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": [4, 5, 6]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_constant_columns"] is False


def test_quality_flags_high_cardinality_categorical():
    df = pd.DataFrame({
        "id": range(1000),
        "high_card": [f"val_{i}" for i in range(1000)],
        "normal_cat": ["X"] * 1000
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_high_cardinality_categoricals"] is True


def test_quality_flags_high_cardinality_not_triggered_on_small_dataset():
    df = pd.DataFrame({
        "small_cat": [f"v{i}" for i in range(5)] + [f"v{i}" for i in range(5)]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_high_cardinality_categoricals"] is False

    df2 = pd.DataFrame({
        "small_cat": [f"v{i}" for i in range(6)] + [f"v{i}" for i in range(4)]
    })
    summary2 = summarize_dataset(df2)
    missing_df2 = missing_table(df2)
    flags2 = compute_quality_flags(summary2, missing_df2, df2)
    assert flags2["has_high_cardinality_categoricals"] is True


def test_quality_flags_suspicious_id_duplicates():
    df = pd.DataFrame({
        "user_id": [1, 2, 2, 4],
        "value": [10, 20, 30, 40]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_suspicious_id_duplicates"] is True


def test_quality_flags_no_id_duplicates():
    df = pd.DataFrame({
        "order_id": [101, 102, 103, 104],
        "value": [1, 2, 3, 4]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_suspicious_id_duplicates"] is False


def test_quality_flags_id_duplicates_ignored_if_no_id_column():
    df = pd.DataFrame({
        "x": [1, 2, 2, 3],
        "y": ["a", "b", "c", "d"]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_suspicious_id_duplicates"] is False


def test_quality_flags_many_zero_values():
    df = pd.DataFrame({
        "a": [0, 0, 0, 0, 1],
        "b": [0, 0, 0, 0, 0],
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_many_zero_values"] is True


def test_quality_flags_not_many_zeros():
    df = pd.DataFrame({
        "a": [0, 1, 2, 3, 4]
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_many_zero_values"] is False


def test_quality_flags_all_heuristics_combined():
    df = pd.DataFrame({
        "const": ["X"] * 200,
        "high_card": [f"v{i}" for i in range(200)],
        "user_id": [1]*100 + [2]*100,
        "mostly_zeros": [0]*180 + [1]*20,
        "missing_col": [None]*150 + [1]*50,
    })
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)

    assert flags["has_constant_columns"] is True
    assert flags["has_high_cardinality_categoricals"] is True
    assert flags["has_suspicious_id_duplicates"] is True
    assert flags["has_many_zero_values"] is True
    assert flags["too_many_missing"] is True
    assert flags["quality_score"] < 0.5