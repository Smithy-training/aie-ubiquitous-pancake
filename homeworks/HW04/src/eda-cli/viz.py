from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PathLike = Union[str, Path]


def _ensure_dir(path: PathLike) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def plot_histograms_per_column(
    df: pd.DataFrame,
    out_dir: PathLike,
    max_columns: int = 6,
    bins: int = 20,
) -> List[Path]:
    """
    Для числовых колонок строит по отдельной гистограмме.
    Возвращает список путей к PNG.
    """
    out_dir = _ensure_dir(out_dir)
    numeric_df = df.select_dtypes(include="number")

    paths: List[Path] = []
    for i, name in enumerate(numeric_df.columns[:max_columns]):
        s = numeric_df[name].dropna()
        if s.empty:
            continue

        fig, ax = plt.subplots()
        ax.hist(s.values, bins=bins)
        ax.set_title(f"Histogram of {name}")
        ax.set_xlabel(name)
        ax.set_ylabel("Count")
        fig.tight_layout()

        out_path = out_dir / f"hist_{i+1}_{name}.png"
        fig.savefig(out_path)
        plt.close(fig)

        paths.append(out_path)

    return paths


def plot_missing_matrix(df: pd.DataFrame, out_path: PathLike) -> Path:
    """
    Простая визуализация пропусков: где True=пропуск, False=значение.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        # Рисуем пустой график
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Empty dataset", ha="center", va="center")
        ax.axis("off")
    else:
        mask = df.isna().values
        fig, ax = plt.subplots(figsize=(min(12, df.shape[1] * 0.4), 4))
        ax.imshow(mask, aspect="auto", interpolation="none")
        ax.set_xlabel("Columns")
        ax.set_ylabel("Rows")
        ax.set_title("Missing values matrix")
        ax.set_xticks(range(df.shape[1]))
        ax.set_xticklabels(df.columns, rotation=90, fontsize=8)
        ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_correlation_heatmap(df: pd.DataFrame, out_path: PathLike) -> Path:
    """
    Тепловая карта корреляции числовых признаков.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Not enough numeric columns for correlation", ha="center", va="center")
        ax.axis("off")
    else:
        corr = numeric_df.corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(min(10, corr.shape[1]), min(8, corr.shape[0])))
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
        ax.set_xticks(range(corr.shape[1]))
        ax.set_xticklabels(corr.columns, rotation=90, fontsize=8)
        ax.set_yticks(range(corr.shape[0]))
        ax.set_yticklabels(corr.index, fontsize=8)
        ax.set_title("Correlation heatmap")
        fig.colorbar(im, ax=ax, label="Pearson r")

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path

def plot_categorical_bar(
    df: pd.DataFrame,
    column: str,
    out_path: PathLike,
    top_n: Optional[int] = None,
) -> Path:
    """
    Строит bar chart для категориальной колонки.
    Если top_n задан — отображает только top-N категорий.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    s = df[column].dropna()
    if s.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"No data in '{column}'", ha="center", va="center")
        ax.axis("off")
    else:
        value_counts = s.value_counts()
        if top_n is not None:
            value_counts = value_counts.head(top_n)

        fig, ax = plt.subplots(figsize=(min(12, max(6, len(value_counts) * 0.5)), 5))
        ax.bar(value_counts.index.astype(str), value_counts.values)
        ax.set_title(f"Count by {column}" + (f" (Top {top_n})" if top_n else ""))
        ax.set_xlabel(column)
        ax.set_ylabel("Count")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()

    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_boxplots(
    df: pd.DataFrame,
    out_path: PathLike,
    max_columns: int = 6,
) -> Path:
    """
    Строит box plots для числовых колонок (максимум max_columns).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_df = df.select_dtypes(include="number")
    numeric_cols = numeric_df.columns[:max_columns]

    if len(numeric_cols) == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No numeric columns", ha="center", va="center")
        ax.axis("off")
    else:
        fig, ax = plt.subplots(figsize=(min(12, max(6, len(numeric_cols) * 1.2)), 5))
        numeric_df[numeric_cols].boxplot(ax=ax)
        ax.set_title("Box plots of numeric columns")
        ax.set_ylabel("Value")
        fig.tight_layout()

    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_top_n_categories(
    df: pd.DataFrame,
    column: str,
    out_path: PathLike,
    top_n: int = 10,
) -> Path:
    """
    Строит bar chart ТОЛЬКО для top-N категорий заданной колонки.
    Аналогичен plot_categorical_bar с top_n, но вынесен отдельно по требованию.
    """
    return plot_categorical_bar(df, column, out_path, top_n=top_n)

def save_top_categories_tables(
    top_cats: Dict[str, pd.DataFrame],
    out_dir: PathLike,
) -> List[Path]:
    """
    Сохраняет top-k категорий по колонкам в отдельные CSV.
    """
    out_dir = _ensure_dir(out_dir)
    paths: List[Path] = []
    for name, table in top_cats.items():
        out_path = out_dir / f"top_values_{name}.csv"
        table.to_csv(out_path, index=False)
        paths.append(out_path)
    return paths
