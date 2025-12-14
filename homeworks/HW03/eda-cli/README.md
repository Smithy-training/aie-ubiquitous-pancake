# eda_cli: мини-EDA для CSV
Небольшое CLI-приложение для базового анализа CSV-файлов.
Используется в рамках Семинара 03 курса «Инженерия ИИ».

Требования
Python 3.11+
uv установлен в систему
Инициализация проекта
В корне проекта (S03):

uv sync

Эта команда:

создаст виртуальное окружение .venv;
установит зависимости из pyproject.toml;
установит сам проект eda-cli в окружение.

Краткий обзор:

uv run eda-cli overview data/example.csv

Параметры:

--sep – разделитель (по умолчанию ,);
--encoding – кодировка (по умолчанию utf-8).

Полный EDA-отчет:

uv run eda-cli report data/example.csv --out-dir reports

В результате в каталоге reports/ появятся:

report.md – основной отчёт в Markdown;
summary.csv – таблица по колонкам;
missing.csv – пропуски по колонкам;
correlation.csv – корреляционная матрица (если есть числовые признаки);
top_categories/*.csv – top-k категорий по строковым признакам;
hist_*.png – гистограммы числовых колонок;
missing_matrix.png – визуализация пропусков;
correlation_heatmap.png – тепловая карта корреляций;
boxplots.png – box plots для числовых признаков;
cat_bar_all.png и cat_bar_top10.png – bar charts для указанной категориальной колонки

--title TEXT
Заголовок отчёта в Markdown
--title "Анализ клиентов"

--max-hist-columns INT
Макс. число гистограмм
--max-hist-columns 5

--top-k-categories INT
Сколько top-значений показывать для категорий
--top-k-categories 10

--min-missing-share FLOAT
Порог доли пропусков для выделения проблемных колонок (от 0.0 до 1.0)
--min-missing-share 0.25

--cat-column TEXT
Имя категориальной колонки для bar charts (например, country)
--cat-column city

--num-box-columns INT
Макс. число числовых колонок для box plots
--num-box-columns 4

Полный вызов:
uv run eda-cli report data/customers.csv \
  --out-dir my_report \
  --title "Анализ пользователей" \
  --cat-column country \
  --min-missing-share 0.2 \
  --top-k-categories 15 \
  --num-box-columns 5

Тесты:

uv run pytest -q