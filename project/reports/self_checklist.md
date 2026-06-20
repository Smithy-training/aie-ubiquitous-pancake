# Самопроверка проекта

Проверка выполнена по чек-листу из приложения А итогового отчета. Статус каждого пункта подтвержден конкретным файлом или исполняемой проверкой.

| № | Критерий | Статус | Подтверждение |
|---:|---|:---:|---|
| 1 | Сервис запускается по инструкции из README и работает | Выполнено | `README.md`, `Dockerfile`, `docker-compose.yml`, `src/app/main.py`; контейнер переходит в `healthy` |
| 2 | `/predict` использует реальную модель, а не заглушку | Выполнено | `src/app/api/predict.py` вызывает `_run_prediction`, который вызывает `PricingModelService.predict` из `src/app/services/model_loader.py` |
| 3 | Есть EDA и хотя бы один эксперимент с метриками | Выполнено | `notebooks/01_eda.ipynb`, `reports/figures/eda_summary.png`, `scripts/evaluate_models.py`, `reports/model_comparison.json` |
| 4 | Есть baseline и улучшенная модель, сравнение по метрикам | Выполнено | Dummy, Linear Regression, Decision Tree и Random Forest сравниваются в `scripts/evaluate_models.py`; результаты сохранены в `reports/model_comparison.json` |
| 5 | Код структурирован в `src/`, а не свален в один ноутбук | Выполнено | `src/app/api`, `src/app/core`, `src/app/models`, `src/app/services` |
| 6 | Есть Dockerfile или внятный сценарий развёртывания | Выполнено | `Dockerfile`, `docker-compose.yml`, раздел «Запуск через Docker» в `README.md` |
| 7 | Есть `.env.example`, нет реальных секретов в репозитории | Выполнено | `.env.example`, `.gitignore`, `.dockerignore`; поиск ключей и паролей совпадений не выявил |
| 8 | Реализованы логи и эндпоинт `/health` | Выполнено | `src/app/core/logger.py`, `src/app/core/metrics.py`, `src/app/api/health.py`; доступны `/health`, `/health/live`, `/health/ready` |
| 9 | Обоснован выбор финальной модели | Выполнено | Раздел 2.4 отчета, `docs/model_card.md`, `artifacts/model_metadata.json`, `reports/model_comparison.json` |
| 10 | README и отчет позволяют понять сценарий демонстрации | Выполнено | Docker-запуск и запрос в `README.md`, разделы 3.2–3.3 и заключение отчета |

## Контрольные команды

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
python scripts/evaluate_models.py
python scripts/export_openapi.py --output docs/openapi.json
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose down
```

Последняя полная проверка: 20.06.2026.
