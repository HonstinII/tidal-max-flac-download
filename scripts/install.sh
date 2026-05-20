#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install ffmpeg and flac."
  exit 1
fi

brew install ffmpeg flac
python3 -m pip install --user streamrip

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "Installed. Run: .venv/bin/python -m uvicorn app.main:app --reload"
