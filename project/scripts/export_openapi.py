import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI schema.")
    parser.add_argument("--output", default="docs/openapi.json")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(app.openapi(), file, ensure_ascii=False, indent=2)

    print(output_path)


if __name__ == "__main__":
    main()
