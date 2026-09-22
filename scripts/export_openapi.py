"""Export the API contract without starting a server."""

import json
from pathlib import Path

from app.main import app

target = Path(__file__).resolve().parents[1] / "contracts/openapi.json"
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
