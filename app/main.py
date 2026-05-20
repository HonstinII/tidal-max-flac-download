from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import setup_status
from .config import default_config
from .tidal_auth import TidalAuthManager
from .tidal_config import write_tidal_auth
from .jobs import DownloadJobManager, JobOptions

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="Tidal Max FLAC Studio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
auth_manager = TidalAuthManager()
job_manager = DownloadJobManager()


class JobRequest(BaseModel):
    urls: list[str]
    output_dir: str | None = None
    concurrency: int = 10
    embed_covers: bool = True
    skip_existing: bool = True


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


@app.post("/api/jobs")
def create_job(request: JobRequest):
    options = JobOptions(
        output_dir=Path(request.output_dir).expanduser() if request.output_dir else None,
        concurrency=request.concurrency,
        embed_covers=request.embed_covers,
        skip_existing=request.skip_existing,
    )
    job = job_manager.create_job(request.urls, options)
    job_manager.start_job(job.job_id)
    return {"job_id": job.job_id, "status": job.status}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        return {"error": "not found"}
    return {"job_id": job.job_id, "status": job.status, "events": job.events}


@app.get("/api/jobs/{job_id}/events")
def get_job_events(job_id: str):
    return StreamingResponse(
        job_manager.events(job_id),
        media_type="text/event-stream",
    )
