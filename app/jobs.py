import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from typing import Iterable

from .config import default_config
from .covers import embed_cover
from .downloader import DownloadOptions, download_track_as_flac, parse_flac_dash_manifest
from .folders import open_folder, pick_folder
from .lyrics import embed_lyrics
from .tidal_api import TidalApi, parse_tidal_url
from .tidal_config import read_tidal_auth


@dataclass(frozen=True)
class JobOptions:
    output_dir: Path | None = None
    concurrency: int = 10
    embed_covers: bool = True
    embed_lyrics: bool = True
    skip_existing: bool = True


@dataclass
class DownloadJob:
    job_id: str
    urls: list[str]
    options: JobOptions
    status: str = "queued"
    events: list[dict] = field(default_factory=list)
    event_queue: Queue = field(default_factory=Queue)


class DownloadJobManager:
    def __init__(self):
        self.jobs: dict[str, DownloadJob] = {}
        self.lock = threading.Lock()

    def create_job(self, urls: list[str], options: JobOptions) -> DownloadJob:
        job = DownloadJob(job_id=str(uuid.uuid4()), urls=urls, options=options)
        self.jobs[job.job_id] = job
        self.emit(job.job_id, {"stage": "created", "job_id": job.job_id})
        return job

    def get_job(self, job_id: str) -> DownloadJob | None:
        return self.jobs.get(job_id)

    def emit(self, job_id: str, event: dict) -> None:
        job = self.jobs[job_id]
        event = {"time": time.time(), **event}
        with self.lock:
            job.events.append(event)
            job.event_queue.put(event)

    def start_job(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()

    def events(self, job_id: str) -> Iterable[str]:
        job = self.jobs[job_id]
        for event in job.events:
            yield _sse(event)
        while job.status not in {"complete", "failed"}:
            event = job.event_queue.get()
            yield _sse(event)

    def _run_job(self, job_id: str) -> None:
        job = self.jobs[job_id]
        job.status = "running"
        self.emit(job_id, {"stage": "running"})
        try:
            auth = read_tidal_auth(default_config().streamrip_config)
            api = TidalApi(auth)
            output_dir = job.options.output_dir or default_config().output_dir
            headers = {"authorization": f"Bearer {auth.access_token}"}
            for url in job.urls:
                try:
                    ref = parse_tidal_url(url)
                    self.emit(job_id, {"stage": "fetching", "url": url})
                    tracks = api.resolve(ref)
                    self.emit(job_id, {"stage": "fetched", "url": url, "count": len(tracks)})
                    for track in tracks:
                        self.emit(
                            job_id,
                            {
                                "stage": "track",
                                "track_id": track.track_id,
                                "title": track.title,
                                "artist": track.artist,
                            },
                        )
                        lyrics = ""
                        if job.options.embed_lyrics:
                            try:
                                lyrics = api.get_lyrics(track.track_id)
                            except Exception as error:
                                self.emit(
                                    job_id,
                                    {
                                        "stage": "lyrics_unavailable",
                                        "track_id": track.track_id,
                                        "message": str(error),
                                    },
                                )
                        playback = api.get(
                            f"tracks/{track.track_id}/playbackinfopostpaywall",
                            {
                                "audioquality": "HI_RES",
                                "playbackmode": "STREAM",
                                "assetpresentation": "FULL",
                            },
                        )
                        manifest = parse_flac_dash_manifest(playback["manifest"])
                        result = download_track_as_flac(
                            track,
                            manifest,
                            DownloadOptions(
                                output_dir=output_dir,
                                concurrency=job.options.concurrency,
                                skip_existing=job.options.skip_existing,
                            ),
                            headers,
                            lambda event: self.emit(job_id, event),
                        )
                        if job.options.embed_covers:
                            embed_cover(result.output_path, track.cover_id, output_dir / ".covers")
                            self.emit(
                                job_id,
                                {"stage": "cover", "track_id": track.track_id},
                            )
                        if job.options.embed_lyrics:
                            if embed_lyrics(result.output_path, lyrics):
                                self.emit(job_id, {"stage": "lyrics", "track_id": track.track_id})
                except Exception as error:
                    self.emit(
                        job_id,
                        {"stage": "error", "url": url, "message": str(error)},
                    )
            job.status = "complete"
            self.emit(job_id, {"stage": "complete"})
        except Exception as error:
            job.status = "failed"
            self.emit(job_id, {"stage": "failed", "message": str(error)})


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"
