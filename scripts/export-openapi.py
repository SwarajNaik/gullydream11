"""Export OpenAPI spec from the FastAPI app (offline — no running server needed)."""

import json
import sys

# Import the app to get its OpenAPI schema
from src.app import app

spec = app.openapi()

with open("openapi.json", "w") as f:
    json.dump(spec, f, indent=2)

print(f"OpenAPI spec exported to openapi.json ({len(json.dumps(spec))} bytes)")
sys.exit(0)
