"""
Simple client to test the /quality and /quality-from-csv endpoints.
"""

import asyncio
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_quality_endpoint(client: httpx.AsyncClient) -> dict:
    """Test /quality with synthetic metadata."""
    payload = {
        "n_rows": 5000,
        "n_cols": 20,
        "max_missing_share": 0.05,
        "numeric_cols": 10,
        "categorical_cols": 10,
    }
    resp = await client.post(f"{BASE_URL}/quality", json=payload)
    data = resp.json()
    return {
        "endpoint": "/quality",
        "status": resp.status_code,
        "quality_score": data.get("quality_score", "N/A"),
        "latency_ms": round(data.get("latency_ms", 0), 2),
        "ok_for_model": data.get("ok_for_model", False),
    }

async def test_quality_from_csv(client: httpx.AsyncClient, csv_path: str) -> dict:
    """Test /quality-from-csv with a real CSV file."""
    path = Path(csv_path)
    if not path.exists():
        return {
            "endpoint": "/quality-from-csv",
            "status": "ERROR",
            "quality_score": "N/A",
            "latency_ms": 0,
            "ok_for_model": False,
            "error": f"File not found: {csv_path}",
        }

    with open(path, "rb") as f:
        files = {"file": (path.name, f, "text/csv")}
        resp = await client.post(f"{BASE_URL}/quality-from-csv", files=files)

    if resp.status_code == 200:
        data = resp.json()
        return {
            "endpoint": "/quality-from-csv",
            "status": resp.status_code,
            "quality_score": data.get("quality_score", "N/A"),
            "latency_ms": round(data.get("latency_ms", 0), 2),
            "ok_for_model": data.get("ok_for_model", False),
        }
    else:
        return {
            "endpoint": "/quality-from-csv",
            "status": resp.status_code,
            "quality_score": "N/A",
            "latency_ms": 0,
            "ok_for_model": False,
            "error": resp.text,
        }

async def main():
    csv_files = [
        "data/example.csv",
        "data/customers.csv",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        results = []
        results.append(await test_quality_endpoint(client))
        for csv in csv_files:
            if Path(csv).exists():
                results.append(await test_quality_from_csv(client, csv))
            else:
                print(f"⚠️ Skipping {csv} (file not found)")

        print("\n" + "=" * 80)
        print(f"{'Endpoint':<25} {'Status':<8} {'Score':<8} {'Latency (ms)':<12} {'OK?'}")
        print("-" * 80)

        for r in results:
            if "error" in r:
                print(f"{r['endpoint']:<25} ERROR    {'N/A':<8} {'N/A':<12} N/A   → {r['error']}")
            else:
                print(
                    f"{r['endpoint']:<25} "
                    f"{r['status']:<8} "
                    f"{r['quality_score']:<8} "
                    f"{r['latency_ms']:<12} "
                    f"{'WellDONE' if r['ok_for_model'] else 'ERROR'}"
                )
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())