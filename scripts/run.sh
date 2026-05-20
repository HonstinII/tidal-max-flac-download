#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
  echo "Missing .venv. Run ./scripts/install.sh first."
  exit 1
fi

URL="http://127.0.0.1:8000"

if command -v open >/dev/null 2>&1; then
  (sleep 1 && open "$URL") >/dev/null 2>&1 &
fi

echo "Starting Tidal Max FLAC Studio at $URL"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
