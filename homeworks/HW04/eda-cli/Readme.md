uv run uvicorn eda_cli.api:app

http://127.0.0.1:8000/docs

curl -X POST http://127.0.0.1:8000/quality-from-csb -F "file=@data/example.csv"