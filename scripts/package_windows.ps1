$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (!(Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller

.\.venv\Scripts\pyinstaller.exe `
  --noconfirm `
  --windowed `
  --name "Tidal Max FLAC Studio" `
  --icon "assets/app_icon.ico" `
  --add-data "app/static;app/static" `
  --add-data "app/tools;app/tools" `
  --hidden-import "uvicorn.logging" `
  --hidden-import "uvicorn.loops" `
  --hidden-import "uvicorn.loops.auto" `
  --hidden-import "uvicorn.protocols" `
  --hidden-import "uvicorn.protocols.http" `
  --hidden-import "uvicorn.protocols.http.auto" `
  --hidden-import "uvicorn.protocols.websockets" `
  --hidden-import "uvicorn.protocols.websockets.auto" `
  --hidden-import "uvicorn.lifespan" `
  --hidden-import "uvicorn.lifespan.on" `
  app/desktop.py

Write-Host "Built: dist\Tidal Max FLAC Studio\Tidal Max FLAC Studio.exe"
