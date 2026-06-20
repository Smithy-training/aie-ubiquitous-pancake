# AI Pricing Service

Интеллектуальный веб-сервис для прогноза товарного спроса и расчета рекомендованной цены. Проект объединяет обученную ML-модель, контролируемую бизнес-логику, REST API, веб-интерфейс, проверку модельных артефактов, метрики Prometheus и контейнерное развертывание.

Сервис получает параметры товара и контекст прогноза, оценивает ожидаемый спрос в единицах, а затем рассчитывает ценовую рекомендацию относительно текущей базовой цены. Готовая модель поставляется в `artifacts/`, поэтому для запуска приложения повторное обучение не требуется.

## Запуск через Docker

Требования: Docker Desktop или Docker Engine с Docker Compose v2.

Из корня проекта выполните:

```powershell
docker compose up --build -d
docker compose ps
```

После запуска доступны:

| Адрес | Назначение |
|---|---|
| <http://localhost:8000/> | веб-интерфейс |
| <http://localhost:8000/docs> | Swagger UI |
| <http://localhost:8000/health/ready> | готовность API и модели |
| <http://localhost:8000/v1/model/info> | сведения о модели |
| <http://localhost:8000/metrics> | метрики приложения |
| <http://localhost:9090> | Prometheus |

Быстрая проверка API:

```powershell
Invoke-RestMethod http://localhost:8000/health/ready

$body = @{
    product_id = "ELEC-100500"
    horizon_days = 3
    current_base_price = 1500.0
    is_weekend = $true
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/v1/predict `
    -Method Post `
    -ContentType application/json `
    -Body $body
```

Просмотр логов и остановка:

```powershell
docker compose logs -f ai-pricing-service
docker compose down
```

Для запуска только API, без Prometheus:

```powershell
docker build -t ai-pricing-service:1.0.0 .
docker run --rm -p 8000:8000 ai-pricing-service:1.0.0
```

Healthcheck контейнера обращается к `/health/ready`. Контейнер переходит в состояние `healthy` только после загрузки и проверки модельных артефактов.

## Что делает сервис

Основной сценарий обработки запроса:

```text
product_id + horizon_days + current_base_price + is_weekend
                              |
                              v
             DictVectorizer -> RandomForestRegressor
                              |
                              v
                    predicted_demand_units
                              |
                              v
        бизнес-логика цены + оценка уверенности
                              |
                              v
             recommended_price + confidence_score
```

Сервис решает две связанные, но отдельные задачи:

1. ML-модель прогнозирует спрос `predicted_demand_units`.
2. Бизнес-логика рассчитывает `recommended_price`, используя прогноз спроса и ограничивая изменение относительно базовой цены диапазоном от `-12%` до `+18%`.

`confidence_score` учитывает разброс прогнозов деревьев, положение цены относительно обучающего диапазона и длину горизонта. Если значение ниже настроенного порога, успешный ответ дополнительно содержит предупреждение.

Основные возможности:

- одиночный и пакетный прогноз до 50 позиций;
- обработка неизвестных `product_id` без остановки сервиса;
- инженерное объяснение факторов конкретного прогноза;
- история последних 50 прогнозов в памяти процесса;
- проверка версии, контракта и SHA-256 модельных артефактов;
- readiness-проба с реальным тестовым инференсом;
- структурированные JSON-логи и сквозной `X-Request-ID`;
- HTTP-метрики, latency и ML-метрики в формате Prometheus.

## Модель и результаты

Используется sklearn pipeline:

```text
DictVectorizer -> RandomForestRegressor
```

Модель обучена на воспроизводимом синтетическом наборе `synthetic-pricing-v1-seed-42`: 1000 наблюдений, пять товаров, четыре входных признака и целевая переменная `demand_units`. Данные разделяются на обучающую и тестовую части в соотношении 80/20 с `random_state=42`.

Сравнение на одной отложенной выборке:

| Модель | MAE | RMSE |
|---|---:|---:|
| `DummyRegressor` | 11.0784 | 13.4425 |
| `LinearRegression` | 2.9439 | 3.8456 |
| `DecisionTreeRegressor` | 2.8489 | 3.6965 |
| **`RandomForestRegressor`** | **2.3240** | **2.9570** |

Random Forest уменьшает MAE примерно на 79% относительно константного baseline и показывает лучшие значения обеих метрик среди проверенных вариантов. Расчет воспроизводится командой:

```powershell
python scripts/evaluate_models.py
```

Результат сохраняется в `reports/model_comparison.json`. Параметры и контрольные суммы рабочей модели находятся в `artifacts/model_metadata.json`.

Синтетический набор используется для проверки архитектуры и полного ML-пайплайна. Полученные метрики не характеризуют качество на реальных продажах.

## Архитектура и надежность

Приложение разделено на HTTP-маршруты, конфигурацию и наблюдаемость, Pydantic-контракты и сервис загрузки модели. Обучение выполняется отдельно от API: runtime-контейнер получает готовые версионированные артефакты и не изменяет их.

При старте проверяются:

- версия модели, scaler и metadata;
- тип модели, порядок признаков и целевая переменная;
- SHA-256 модели и вспомогательного артефакта;
- возможность выполнить тестовый прогноз.

Если проверка не пройдена, `/health/ready` возвращает ошибку готовности и контейнер не получает статус `healthy`. Основные сценарии API, контракты модели, метрики, конфигурация и веб-интерфейс покрыты автоматизированными тестами.

## API

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/` | веб-интерфейс |
| `POST` | `/v1/predict` | одиночный прогноз |
| `POST` | `/predict` | совместимый маршрут одиночного прогноза |
| `POST` | `/v1/batch-predict` | пакет до 50 прогнозов |
| `POST` | `/v1/explain` | прогноз с пояснением входных признаков |
| `GET` | `/v1/predictions/recent` | последние 50 прогнозов текущего процесса |
| `GET` | `/v1/model/info` | контракт и метаданные модели |
| `GET` | `/version` | версии сервиса, API и модели |
| `GET` | `/health` | базовая проверка состояния |
| `GET` | `/health/live` | проверка работы процесса |
| `GET` | `/health/ready` | проверка готовности модели |
| `GET` | `/metrics` | метрики Prometheus |

Тело запроса `POST /v1/predict`:

```json
{
  "product_id": "ELEC-100500",
  "horizon_days": 3,
  "current_base_price": 1500.0,
  "is_weekend": true
}
```

Ограничения:

- `product_id` - непустая строка;
- `horizon_days` - целое число от 1 до 14;
- `current_base_price` - число больше нуля;
- `is_weekend` - логическое значение, по умолчанию `false`.

Полный интерактивный контракт доступен в Swagger UI. Статическая схема находится в `docs/openapi.json`.

## Локальный запуск

Требуется Python 3.10 или новее.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8000
```

Для Linux и macOS команда активации окружения: `source .venv/bin/activate`.

## Конфигурация

Основные настройки находятся в `configs/config.yaml`. Для локального переопределения скопируйте `.env.example` в `.env`. Переменные окружения имеют формат `СЕКЦИЯ__ПАРАМЕТР`, например:

```powershell
$env:APP__ENV = "local"
$env:ML__MIN_CONFIDENCE_THRESHOLD = "0.7"
```

Пути к модели, scaler и метаданным задаются параметрами `ML__MODEL_PATH`, `ML__SCALER_PATH` и `ML__METADATA_PATH`. Относительные пути разрешаются от корня проекта.

## Проверка проекта

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
docker compose config --quiet
docker build -t ai-pricing-service:check .
```

Обновление статической OpenAPI-схемы:

```powershell
python scripts/export_openapi.py --output docs/openapi.json
```

CI выполняет lint, тесты, проверку Compose и сборку Docker-образа.

## Структура проекта

```text
ai-pricing-service/
|-- src/app/
|   |-- api/                 # HTTP-маршруты и веб-интерфейс
|   |-- core/                # конфигурация, логирование и метрики
|   |-- models/              # Pydantic-схемы
|   |-- services/            # загрузка модели и inference
|   `-- main.py              # FastAPI-приложение
|-- artifacts/               # модель, scaler и метаданные
|-- configs/config.yaml
|-- docs/                    # OpenAPI, model card и описание AI
|-- notebooks/01_eda.ipynb  # воспроизводимый разведочный анализ данных
|-- prometheus/prometheus.yml
|-- reports/                 # метрики, графики и карта соответствия чек-листу
|-- scripts/                 # обучение, оценка моделей и экспорт OpenAPI
|-- tests/
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- requirements-dev.txt
```

Дополнительная документация: `docs/model_card.md`, `docs/ai_usage.md` и `reports/self_checklist.md`.
