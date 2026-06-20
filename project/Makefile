.PHONY: install install-dev train test lint run openapi docker-build docker-compose-config

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

train:
	python scripts/train_model.py --output-dir artifacts --rows 1000 --seed 42

test:
	pytest

lint:
	ruff check .

run:
	uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8000

openapi:
	python scripts/export_openapi.py --output docs/openapi.json

docker-build:
	docker build -t ai-pricing-service:1.0.0 .

docker-compose-config:
	docker compose config
