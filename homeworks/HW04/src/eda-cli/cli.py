from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from .core import (
    DatasetSummary,
    compute_quality_flags,
    correlation_matrix,
    flatten_summary_for_print,
    missing_table,
    summarize_dataset,
    top_categories,
)
from .viz import (
    plot_correlation_heatmap,
    plot_missing_matrix,
    plot_histograms_per_column,
    save_top_categories_tables,
)

app = typer.Typer(help="Мини-CLI для EDA CSV-файлов")


def _load_csv(
    path: Path,
    sep: str = ",",
    encoding: str = "utf-8",
) -> pd.DataFrame:
    if not path.exists():
        raise typer.BadParameter(f"Файл '{path}' не найден")
    try:
        return pd.read_csv(path, sep=sep, encoding=encoding)
    except Exception as exc:  # noqa: BLE001
        raise typer.BadParameter(f"Не удалось прочитать CSV: {exc}") from exc


@app.command()
def overview(
    path: str = typer.Argument(..., help="Путь к CSV-файлу."),
    sep: str = typer.Option(",", help="Разделитель в CSV."),
    encoding: str = typer.Option("utf-8", help="Кодировка файла."),
) -> None:
    """
    Напечатать краткий обзор датасета:
    - размеры;
    - типы;
    - простая табличка по колонкам.
    """
    df = _load_csv(Path(path), sep=sep, encoding=encoding)
    summary: DatasetSummary = summarize_dataset(df)
    summary_df = flatten_summary_for_print(summary)

    typer.echo(f"Строк: {summary.n_rows}")
    typer.echo(f"Столбцов: {summary.n_cols}")
    typer.echo("\nКолонки:")
    typer.echo(summary_df.to_string(index=False))


@app.command()
def report(
    path: str = typer.Argument(..., help="Путь к CSV-файлу."),
    out_dir: str = typer.Option("reports", help="Каталог для отчёта."),
    sep: str = typer.Option(",", help="Разделитель в CSV."),
    encoding: str = typer.Option("utf-8", help="Кодировка файла."),
    max_hist_columns: int = typer.Option(6, help="Максимум числовых колонок для гистограмм."),
    top_k_categories: int = typer.Option(5, help="Сколько топ-значений показывать для категориальных признаков."),
    title: str = typer.Option("EDA-отчёт", help="Заголовок отчёта в Markdown."),
    min_missing_share: float = typer.Option(0.1, help="Порог доли пропусков: колонки с большим значением считаются проблемными."),
    cat_column: Optional[str] = typer.Option(
        None,
        help="Категориальная колонка для bar chart и top-N анализа (например, 'country')."
    ),
    num_box_columns: int = typer.Option(6, help="Максимум числовых колонок для box plots."),
) -> None:
    """
    Сгенерировать полный EDA-отчёт:
    - текстовый overview и summary по колонкам (CSV/Markdown);
    - статистика пропусков;
    - корреляционная матрица;
    - top-k категорий по категориальным признакам;
    - картинки: гистограммы, матрица пропусков, heatmap корреляции.
    """
    if not (0.0 <= min_missing_share <= 1.0):
        raise typer.BadParameter("--min-missing-share must be between 0.0 and 1.0")

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    df = _load_csv(Path(path), sep=sep, encoding=encoding)

    # 1. Обзор с параметрами
    summary = summarize_dataset(df)
    summary_df = flatten_summary_for_print(summary)
    missing_df = missing_table(df)
    corr_df = correlation_matrix(df)
    top_cats = top_categories(df, max_columns=5, top_k=top_k_categories)  # max_columns kept at 5 or make it configurable too?

    # 2. Качество данных
    quality_flags = compute_quality_flags(summary, missing_df, df)

    # 3. Сохраняем табличные артефакты
    summary_df.to_csv(out_root / "summary.csv", index=False)
    if not missing_df.empty:
        missing_df.to_csv(out_root / "missing.csv", index=True)
    if not corr_df.empty:
        corr_df.to_csv(out_root / "correlation.csv", index=True)
    save_top_categories_tables(top_cats, out_root / "top_categories")

    # 4. Markdown-отчёт
    md_path = out_root / "report.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Исходный файл: `{Path(path).name}`\n\n")
        f.write(f"Строк: **{summary.n_rows}**, столбцов: **{summary.n_cols}**\n\n")

        f.write("## Настройки отчёта\n\n")
        f.write(f"- Макс. колонок для гистограмм: `{max_hist_columns}`\n")
        f.write(f"- Топ категорий на признак: `{top_k_categories}`\n")
        f.write(f"- Порог пропусков для проблемных колонок: `{min_missing_share:.1%}`\n\n")

        f.write("## Качество данных (эвристики)\n\n")
        f.write(f"- Оценка качества: **{quality_flags['quality_score']:.2f}**\n")
        f.write(f"- Макс. доля пропусков по колонке: **{quality_flags['max_missing_share']:.2%}**\n")
        f.write(f"- Слишком мало строк: **{quality_flags['too_few_rows']}**\n")
        f.write(f"- Слишком много колонок: **{quality_flags['too_many_columns']}**\n")
        f.write(f"- Слишком много пропусков: **{quality_flags['too_many_missing']}**\n")
        f.write(f"- Есть константные колонки: **{quality_flags['has_constant_columns']}**\n")
        f.write(f"- Есть категориальные колонки с высокой кардинальностью: **{quality_flags['has_high_cardinality_categoricals']}**\n")
        f.write(f"- Подозрение на дубликаты в ID-колонках: **{quality_flags['has_suspicious_id_duplicates']}**\n")
        f.write(f"- Много нулей в числовых данных: **{quality_flags['has_many_zero_values']}**\n\n")

        # New: List problematic columns based on min_missing_share
        problematic_missing_cols = []
        if not missing_df.empty:
            problematic_missing_cols = missing_df[missing_df["missing_share"] >= min_missing_share].index.tolist()
        if problematic_missing_cols:
            f.write("## Проблемные колонки (по пропускам)\n\n")
            f.write("Следующие колонки имеют долю пропусков ≥ " + f"`{min_missing_share:.1%}`:\n\n")
            for col in problematic_missing_cols:
                share = missing_df.loc[col, "missing_share"]
                f.write(f"- `{col}` ({share:.2%})\n")
            f.write("\n")
        else:
            f.write("## Проблемные колонки (по пропускам)\n\n")
            f.write("Нет колонок с долей пропусков ≥ " + f"`{min_missing_share:.1%}`.\n\n")

        f.write("## Колонки\n\n")
        f.write("См. файл `summary.csv`.\n\n")

        f.write("## Пропуски\n\n")
        if missing_df.empty:
            f.write("Пропусков нет или датасет пуст.\n\n")
        else:
            f.write("См. файлы `missing.csv` и `missing_matrix.png`.\n\n")

        f.write("## Корреляция числовых признаков\n\n")
        if corr_df.empty:
            f.write("Недостаточно числовых колонок для корреляции.\n\n")
        else:
            f.write("См. `correlation.csv` и `correlation_heatmap.png`.\n\n")

        f.write("## Категориальные признаки\n\n")
        if not top_cats:
            f.write("Категориальные/строковые признаки не найдены.\n\n")
        else:
            f.write(f"Топ-{top_k_categories} значений для категориальных признаков.\n")
            f.write("См. файлы в папке `top_categories/`.\n\n")

        f.write("## Гистограммы числовых колонок\n\n")
        f.write(f"Показано максимум первых `{max_hist_columns}` числовых колонок.\n")
        f.write("См. файлы `hist_*.png`.\n")

    # 5. Генерация графиков с параметрами
    plot_histograms_per_column(df, out_root, max_columns=max_hist_columns)
    plot_missing_matrix(df, out_root / "missing_matrix.png")
    plot_correlation_heatmap(df, out_root / "correlation_heatmap.png")

    typer.echo(f"Отчёт сгенерирован в каталоге: {out_root}")
    typer.echo(f"- Основной markdown: {md_path}")
    typer.echo("- Табличные файлы: summary.csv, missing.csv, correlation.csv, top_categories/*.csv")
    typer.echo("- Графики: hist_*.png, missing_matrix.png, correlation_heatmap.png")


if __name__ == "__main__":
    app()
