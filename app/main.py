import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import setup_status
from .config import default_config
from .tidal_auth import TidalAuthManager
from .tidal_config import clear_tidal_auth, write_tidal_auth
from .jobs import DownloadJobManager, JobOptions
from .folders import open_folder, pick_folder, reveal_file
from .installer import InstallJobManager, extract_bundled_flac
from .storage import AppDatabase
from .tidal_api import TidalApi, TrackItem, parse_tidal_url
from .tidal_config import read_tidal_auth
from .updater import check_for_update, download_update_asset

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="Tidal Max FLAC Studio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
auth_manager = TidalAuthManager()
install_manager = InstallJobManager()
database = AppDatabase()
database.initialize()
job_manager = DownloadJobManager(database=database)


class JobRequest(BaseModel):
    urls: list[str]
    output_dir: str | None = None
    concurrency: int = 10
    embed_covers: bool = True
    embed_lyrics: bool = True
    audio_quality: str = "max"
    allow_lossy_audio: bool = False
    write_lrc: bool = False
    save_cover_file: bool = False
    cover_file_strategy: str = "skip"
    lyrics_mode: str = "auto"
    skip_existing: bool = True


class PreviewRequest(BaseModel):
    urls: list[str]


class QueueRequest(BaseModel):
    urls: list[str]
    output_dir: str | None = None
    concurrency: int = 10
    embed_covers: bool = True
    embed_lyrics: bool = True
    audio_quality: str = "max"
    allow_lossy_audio: bool = False
    write_lrc: bool = False
    save_cover_file: bool = False
    cover_file_strategy: str = "skip"
    lyrics_mode: str = "auto"
    skip_existing: bool = True
    existing_strategy: str = "skip"
    album_template: str = "{album_artist}/{album} ({year})"
    filename_template: str = "{track_number}. {artist} - {title}"
    single_filename_template: str = "{artist} - {title}"


class FolderRequest(BaseModel):
    path: str | None = None


class RetryRequest(BaseModel):
    allow_lossy_audio: bool = False


class UpdateDownloadRequest(BaseModel):
    asset_url: str
    asset_name: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/update/check")
def check_update():
    info = check_for_update()
    return asdict(info) if is_dataclass(info) else info


@app.post("/api/update/download")
def download_update(request: UpdateDownloadRequest):
    path = download_update_asset(request.asset_url, request.asset_name)
    open_folder(path.parent)
    return {"ok": True, "path": str(path)}


@app.get("/api/setup/status")
def get_setup_status():
    return setup_status()


def preview_track(track: TrackItem) -> dict:
    return {
        "track_id": track.track_id,
        "title": track.title,
        "artist": track.artist,
        "album_title": track.album_title,
        "album_artist": track.album_artist,
        "album_year": track.album_year,
        "track_number": track.track_number,
        "cover_id": track.cover_id,
        "duration_seconds": track.duration_seconds,
        "total_tracks": track.total_tracks,
        "disc_number": track.disc_number,
        "total_discs": track.total_discs,
        "copyright": track.copyright,
        "isrc": track.isrc,
        "upc": track.upc,
    }


def preview_error_message(error: Exception) -> str:
    status_code = getattr(getattr(error, "response", None), "status_code", None)
    raw = str(error)
    if status_code == 401 or ("401" in raw and "Unauthorized" in raw):
        return "402, Tidal 授权已失效，请重新绑定账号。"
    return raw


@app.post("/api/preview")
def preview_urls(request: PreviewRequest):
    auth = read_tidal_auth(default_config().streamrip_config)
    api = TidalApi(auth)
    items = []
    errors = []
    for url in request.urls:
        try:
            ref = parse_tidal_url(url)
            tracks = api.resolve(ref)
            first = tracks[0] if tracks else None
            items.append(
                {
                    "source_url": url,
                    "kind": ref.kind,
                    "item_id": ref.item_id,
                    "track_count": len(tracks),
                    "album_title": first.album_title if first else "",
                    "album_artist": first.album_artist if first else "",
                    "album_year": first.album_year if first else "",
                    "tracks": [preview_track(track) for track in tracks],
                }
            )
        except Exception as error:
            errors.append({"url": url, "message": preview_error_message(error)})
    return {"items": items, "errors": errors}


@app.post("/api/queue")
def create_queue(request: QueueRequest):
    auth = read_tidal_auth(default_config().streamrip_config)
    api = TidalApi(auth)
    output_dir = request.output_dir or str(default_config().output_dir)
    run_id = str(uuid.uuid4())
    options = {
        "concurrency": request.concurrency,
        "embed_covers": request.embed_covers,
        "embed_lyrics": request.embed_lyrics,
        "audio_quality": request.audio_quality,
        "allow_lossy_audio": request.allow_lossy_audio,
        "write_lrc": request.write_lrc,
        "save_cover_file": request.save_cover_file,
        "cover_file_strategy": request.cover_file_strategy,
        "lyrics_mode": request.lyrics_mode,
        "existing_strategy": request.existing_strategy,
        "skip_existing": request.skip_existing,
        "album_template": request.album_template,
        "filename_template": request.filename_template,
        "single_filename_template": request.single_filename_template,
    }
    run = database.create_run(run_id, "queued", output_dir, options)
    items = []
    for url in request.urls:
        ref = parse_tidal_url(url)
        for track in api.resolve(ref):
            items.append(
                database.create_queue_item(
                    item_id=str(uuid.uuid4()),
                    run_id=run_id,
                    source_url=url,
                    source_kind=ref.kind,
                    source_id=ref.item_id,
                    track=preview_track(track),
                    status="ready",
                )
            )
    return {"run": run, "items": items}


@app.get("/api/queue")
def get_queue(include_transient: bool = False):
    items = database.list_queue_items()
    if not include_transient:
        items = [item for item in items if item["status"] == "complete"]
    return {"items": items}


@app.post("/api/queue/runs/{run_id}/start")
def start_queue_run(run_id: str):
    job_manager.start_run(run_id)
    return {"run": database.get_run(run_id)}


@app.get("/api/queue/runs/{run_id}/events")
def get_queue_events(run_id: str):
    return StreamingResponse(
        job_manager.queue_events(run_id),
        media_type="text/event-stream",
    )


@app.post("/api/queue/items/{item_id}/retry")
def retry_queue_item(item_id: str, request: RetryRequest | None = None):
    if request and request.allow_lossy_audio:
        item = job_manager.retry_item_with_options(item_id, allow_lossy_audio=True)
    else:
        item = job_manager.retry_item(item_id)
    run = database.get_run(item["run_id"]) if item else None
    return {"item": item, "run": run}


@app.post("/api/queue/runs/{run_id}/pause")
def pause_queue_run(run_id: str):
    return {"run": job_manager.pause_run(run_id)}


@app.post("/api/queue/runs/{run_id}/resume")
def resume_queue_run(run_id: str):
    return {"run": job_manager.resume_run(run_id)}


@app.post("/api/queue/runs/{run_id}/cancel")
def cancel_queue_run(run_id: str):
    return {"run": job_manager.cancel_run(run_id)}


@app.get("/api/history")
def get_history():
    return {"runs": database.list_runs()}


@app.get("/api/logs/{run_id}.txt", response_class=PlainTextResponse)
def export_log(run_id: str):
    run = database.get_run(run_id)
    if not run:
        return "Run not found."
    lines = [
        "Tidal Max FLAC Studio Download Log",
        f"Run: {run['id']}",
        f"Status: {run['status']}",
        f"Output: {run['output_dir']}",
        f"Options: {run['options']}",
        "",
        "Tracks:",
    ]
    for item in database.list_queue_items(run_id):
        lines.extend(
            [
                f"- {item.get('artist') or ''} - {item.get('title') or item.get('track_id')}",
                f"  Status: {item['status']}",
                f"  Output: {item.get('output_path') or ''}",
                f"  Error: {item.get('error') or ''}",
            ]
        )
    return "\n".join(lines)


@app.post("/api/tools/install")
def install_missing_tools():
    status = setup_status()
    job = install_manager.create_job(
        {
            "platform": status["platform"],
            "tools": status["tools_detail"],
            "package_managers": status["package_managers"],
            "manual_commands": status["manual_commands"],
            "manual_urls": status["manual_urls"],
        }
    )
    install_manager.start_job(job.job_id)
    return {"job_id": job.job_id, "status": job.status}


@app.post("/api/tools/bundled-flac")
def use_bundled_flac_tools():
    return extract_bundled_flac()


@app.get("/api/tools/install/{job_id}/events")
def get_install_events(job_id: str):
    return StreamingResponse(
        install_manager.events(job_id),
        media_type="text/event-stream",
    )


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


@app.post("/api/auth/tidal/unbind")
def unbind_tidal_auth():
    clear_tidal_auth(default_config().streamrip_config)
    return {"ok": True}


@app.post("/api/jobs")
def create_job(request: JobRequest):
    options = JobOptions(
        output_dir=Path(request.output_dir).expanduser() if request.output_dir else None,
        concurrency=request.concurrency,
        embed_covers=request.embed_covers,
        embed_lyrics=request.embed_lyrics,
        audio_quality=request.audio_quality,
        allow_lossy_audio=request.allow_lossy_audio,
        write_lrc=request.write_lrc,
        save_cover_file=request.save_cover_file,
        cover_file_strategy=request.cover_file_strategy,
        lyrics_mode=request.lyrics_mode,
        skip_existing=request.skip_existing,
        album_template=getattr(request, "album_template", "{album_artist}/{album} ({year})"),
        filename_template=getattr(request, "filename_template", "{track_number}. {artist} - {title}"),
        single_filename_template=getattr(request, "single_filename_template", "{artist} - {title}"),
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


@app.post("/api/folders/pick")
def pick_output_folder(request: FolderRequest):
    initial = Path(request.path).expanduser() if request.path else default_config().output_dir
    selected = pick_folder(initial)
    return {"path": str(selected) if selected else None}


@app.post("/api/folders/open")
def open_output_folder(request: FolderRequest):
    path = Path(request.path).expanduser() if request.path else default_config().output_dir
    open_folder(path)
    return {"ok": True, "path": str(path)}


@app.post("/api/folders/reveal")
def reveal_output_file(request: FolderRequest):
    if not request.path:
        return {"ok": False}
    path = Path(request.path).expanduser()
    reveal_file(path)
    return {"ok": True, "path": str(path)}
