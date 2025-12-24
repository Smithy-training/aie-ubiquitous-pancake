# Описание изменений
## 1. Основная логика EDA (core.py)

Добавлены 4 новых эвристических правила качества данных в compute_quality_flags:
has_constant_columns
has_high_cardinality_categoricals
has_suspicious_id_duplicates
has_many_zero_values

Обновлен quality score, чтобы налагать штрафы на основе этих флагов.
Теперь функция требует в качестве входных данных исходный DataFrame.

## 2. Улучшения CLI (cli.py)

Добавлены новые опции CLI в отчет eda-cli:
--title: настраиваемый заголовок отчета
--top-k-categories: количество значений верхних категорий
--min-missing-share: порог для пометки проблемных столбцов
--cat-column: категориальный столбец для гистограмм
--num-box-columns: максимальное количество числовых столбцов для бокс-плотов

Обновлен отчет Markdown (report.md) с добавлением:
- Используемые настройки
- Список проблемных столбцов (по доле отсутствующих данных)
- Все новые флаги качества
- Исправлен вызов compute_quality_flags (теперь передает df).

## 3. Новые визуализации (viz.py)

Добавлены 3 новые функции построения графиков:
plot_boxplots(): числовой boxplots.png
plot_categorical_bar(): гистограмма для всех значений в категориальном столбце cat_bar_all.png
plot_top_n_categories(): гистограмма для N лучших значений cat_bar_top10.png

## 4. Конечные точки API (api.py)

Добавлена новый Эндпоинт: POST /quality-flags-from-csv
Принимает загрузку CSV ; Запускает полный конвейер EDA ; Возвращает полный JSON со всеми флагами, оценкой, формой и задержкой

## 5. Тесты (tests/test_core.py)

- Добавлены целенаправленные модульные тесты для всех 4 новых эвристик качества
- Проверены крайние случаи (пороговые границы, отсутствующие столбцы ID и т. д.)
- Обеспечена интеграция всех флагов

## 6. Тестовый клиент (client.py)

Простой асинхронный скрипт для тестирования /quality и /quality-from-csv.
Выводит четкую сводку: эндпоинт, статус, оценка, задержка, OK flag.

# Запуск
```bash
uv sync
uv run pytest-v
```

```bash
uv run eda-cli overview data/example.csv
```

```bash
uv run eda-cli report data/example.csv \
  --out-dir test_report \
  --title "Тестовый отчёт с графиками" \
  --cat-column city \
  --min-missing-share 0.2 \
  --top-k-categories 3 \
  --num-box-columns 2
```

```bash
uv run uvicorn eda_cli.api:app --reload
```

```bash
uv run python client.py
```

Manual test:
```bash
curl -X POST http://127.0.0.1:8000/quality-flags-from-csv \
  -F "file=@data/example.csv" | python -m json.tool
```

```bash
uv run uvicorn eda_cli.api:app

http://127.0.0.1:8000/docs

curl -X POST http://127.0.0.1:8000/quality-from-csb -F "file=@data/example.csv"
```
