from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import setup_status
from .config import default_config
from .tidal_auth import TidalAuthManager
from .tidal_config import write_tidal_auth

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="Tidal Max FLAC Studio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
auth_manager = TidalAuthManager()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/setup/status")
def get_setup_status():
    return setup_status()


@app.post("/api/auth/tidal/start")
def start_tidal_auth():
    session = auth_manager.start()
    return {
        "session_id": session.session_id,
        "url": session.url,
        "expires_in": session.expires_in,
    }


@app.get("/api/auth/tidal/status/{session_id}")
def get_tidal_auth_status(session_id: str):
    result = auth_manager.poll(session_id)
    if result.status == "success" and result.token is not None:
        write_tidal_auth(default_config().streamrip_config, result.token)
    return {
        "status": result.status,
        "message": result.message,
        "token": {
            "user_id": result.token.user_id,
            "country_code": result.token.country_code,
            "token_expiry": result.token.token_expiry,
        }
        if result.token
        else None,
    }
