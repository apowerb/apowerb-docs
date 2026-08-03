#!/usr/bin/env bash
# Refresh api-reference/openapi.json from a running apowerb instance.
#
# Commercial-only routes are stripped so the published reference matches the
# open-source edition. See concepts/editions.mdx.
#
# Usage: ./scripts/sync-openapi.sh https://your-instance.example.com
set -euo pipefail

BASE="${1:?usage: $0 <base-url>}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/api-reference/openapi.json"
VERSION="${APOWERB_VERSION:-0.1.2}"
export OUT VERSION

curl -fsS "${BASE%/}/openapi.json" | python3 - <<'PY'
import json
import os
import sys

spec = json.load(sys.stdin)

COMMERCIAL_TAGS = {"Billing", "usage", "prospection", "campaigns"}
COMMERCIAL_PATH_MARKERS = ("/mfa",)

removed = []
for path in list(spec["paths"]):
    tags = set()
    for _method, operation in spec["paths"][path].items():
        if isinstance(operation, dict):
            tags |= set(operation.get("tags", []))
    if tags & COMMERCIAL_TAGS or any(m in path for m in COMMERCIAL_PATH_MARKERS):
        removed.append(path)
        del spec["paths"][path]

spec["info"] = {
    "title": "apowerb API",
    "description": "REST API of the apowerb agentic framework (open-source edition).",
    "version": os.environ["VERSION"],
    "license": {
        "name": "MIT",
        "url": "https://github.com/apowerb/apowerb/blob/main/LICENSE",
    },
}
spec["servers"] = [
    {"url": "https://api.example.com", "description": "Your apowerb instance"},
    {"url": "http://localhost:8000", "description": "Local stack"},
]

with open(os.environ["OUT"], "w") as handle:
    json.dump(spec, handle, indent=2, ensure_ascii=False)

print(f"{len(spec['paths'])} paths kept, {len(removed)} commercial paths removed")
PY
