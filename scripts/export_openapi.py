"""Dump the FastAPI OpenAPI spec to stdout or a file.

Used by the frontend type generation:
    python scripts/export_openapi.py frontend-react/openapi.json
    cd frontend-react && npm run generate:api
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app  # noqa: E402


def main():
    spec = json.dumps(app.openapi(), indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(spec + "\n", encoding="utf-8")
        print(f"OpenAPI spec written to {sys.argv[1]}")
    else:
        print(spec)


if __name__ == "__main__":
    main()
