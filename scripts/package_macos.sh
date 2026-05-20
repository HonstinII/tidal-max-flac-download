#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt pyinstaller

.venv/bin/pyinstaller \
  --noconfirm \
  --windowed \
  --name "Tidal Max FLAC Studio" \
  --icon "assets/app_icon.icns" \
  --osx-bundle-identifier "com.honstinii.tidalmaxflacstudio" \
  --add-data "app/static:app/static" \
  --hidden-import "uvicorn.logging" \
  --hidden-import "uvicorn.loops" \
  --hidden-import "uvicorn.loops.auto" \
  --hidden-import "uvicorn.protocols" \
  --hidden-import "uvicorn.protocols.http" \
  --hidden-import "uvicorn.protocols.http.auto" \
  --hidden-import "uvicorn.protocols.websockets" \
  --hidden-import "uvicorn.protocols.websockets.auto" \
  --hidden-import "uvicorn.lifespan" \
  --hidden-import "uvicorn.lifespan.on" \
  app/desktop.py

echo "Built: dist/Tidal Max FLAC Studio.app"
