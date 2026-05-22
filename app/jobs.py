import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from typing import Callable, Iterable

import requests

from .config import default_config
from .covers import embed_cover, embed_mp4_cover
from .downloader import DownloadOptions, LossyAudioAvailable, download_track_as_flac, parse_flac_dash_manifest
from .lyrics import embed_lyrics, embed_mp4_lyrics, extract_lyrics_text, write_lrc
from .metadata import has_cover, repair_flac_tags, repair_mp4_tags
from .storage import AppDatabase
from .tidal_api import TidalApi, TrackItem, parse_tidal_url
from .tidal_config import read_tidal_auth


@dataclass(frozen=True)
class JobOptions:
    output_dir: Path | None = None
    concurrency: int = 10
    embed_covers: bool = True
    embed_lyrics: bool = True
    audio_quality: str = "max"
    allow_lossy_audio: bool = False
    write_lrc: bool = False
    lyrics_mode: str = "auto"
    skip_existing: bool = True
    existing_strategy: str | None = None
    album_template: str = "{album_artist}/{album} ({year})"
    filename_template: str = "{track_number}. {artist} - {title}"
    single_filename_template: str = "{artist} - {title}"


@dataclass
class DownloadJob:
    job_id: str
    urls: list[str]
    options: JobOptions
    status: str = "queued"
    events: list[dict] = field(default_factory=list)
    event_queue: Queue = field(default_factory=Queue)


class DownloadJobManager:
    def __init__(
        self,
        database: AppDatabase | None = None,
        auth_reader: Callable[[Path], object] = read_tidal_auth,
        api_factory: Callable[[object], TidalApi] = TidalApi,
        downloader: Callable = download_track_as_flac,
    ):
        self.jobs: dict[str, DownloadJob] = {}
        self.lock = threading.Lock()
        self.database = database or AppDatabase()
        self.database.initialize()
        self.auth_reader = auth_reader
        self.api_factory = api_factory
        self.downloader = downloader
        self.run_queues: dict[str, Queue] = {}
        self.run_events: dict[str, list[dict]] = {}
        self.run_threads: dict[str, threading.Thread] = {}

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

    def emit_run(self, run_id: str, event: dict) -> None:
        event = {"time": time.time(), "run_id": run_id, **event}
        with self.lock:
            self.run_events.setdefault(run_id, []).append(event)
            self.run_queues.setdefault(run_id, Queue()).put(event)

    def start_job(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()

    def start_run(self, run_id: str) -> None:
        if run_id in self.run_threads and self.run_threads[run_id].is_alive():
            return
        self.run_queues.setdefault(run_id, Queue())
        self.run_events.setdefault(run_id, [])
        thread = threading.Thread(target=self._run_queue, args=(run_id,), daemon=True)
        self.run_threads[run_id] = thread
        thread.start()

    def events(self, job_id: str) -> Iterable[str]:
        job = self.jobs[job_id]
        for event in job.events:
            yield _sse(event)
        while job.status not in {"complete", "failed"}:
            event = job.event_queue.get()
            yield _sse(event)

    def queue_events(self, run_id: str) -> Iterable[str]:
        for event in self.run_events.get(run_id, []):
            yield _sse(event)
        while True:
            run = self.database.get_run(run_id)
            if run and run["status"] in {"complete", "failed", "cancelled"}:
                break
            event = self.run_queues.setdefault(run_id, Queue()).get()
            yield _sse(event)

    def _run_job(self, job_id: str) -> None:
        job = self.jobs[job_id]
        run = self.create_run_from_urls(job.urls, job.options, status="queued")
        self.start_run(run["id"])
        job.status = "running"
        self.emit(job_id, {"stage": "running", "run_id": run["id"]})
        for event in self.queue_events(run["id"]):
            payload = json.loads(event.removeprefix("data: ").strip())
            self.emit(job_id, payload)
        run = self.database.get_run(run["id"])
        job.status = "failed" if run and run["status"] == "failed" else "complete"

    def create_run_from_urls(
        self, urls: list[str], options: JobOptions, status: str = "queued"
    ) -> dict:
        auth = self.auth_reader(default_config().streamrip_config)
        api = self.api_factory(auth)
        output_dir = str(options.output_dir or default_config().output_dir)
        existing_strategy = options.existing_strategy or ("skip" if options.skip_existing else "overwrite")
        run_id = str(uuid.uuid4())
        run = self.database.create_run(
            run_id,
            status,
            output_dir,
            {
                "concurrency": options.concurrency,
                "embed_covers": options.embed_covers,
                "embed_lyrics": options.embed_lyrics,
                "audio_quality": options.audio_quality,
                "allow_lossy_audio": options.allow_lossy_audio,
                "write_lrc": options.write_lrc,
                "lyrics_mode": options.lyrics_mode,
                "skip_existing": options.skip_existing,
                "existing_strategy": existing_strategy,
                "album_template": options.album_template,
                "filename_template": options.filename_template,
                "single_filename_template": options.single_filename_template,
            },
        )
        for url in urls:
            ref = parse_tidal_url(url)
            for track in api.resolve(ref):
                self.database.create_queue_item(
                    item_id=str(uuid.uuid4()),
                    run_id=run_id,
                    source_url=url,
                    source_kind=ref.kind,
                    source_id=ref.item_id,
                    track=track_to_dict(track),
                    status="ready",
                )
        return run

    def _run_queue(self, run_id: str) -> None:
        run = self.database.get_run(run_id)
        if not run:
            return
        self.database.update_run(run_id, status="running")
        self.emit_run(run_id, {"stage": "running"})
        auth = self.auth_reader(default_config().streamrip_config)
        api = self.api_factory(auth)
        headers = {"authorization": f"Bearer {auth.access_token}"}
        while True:
            run = self.database.get_run(run_id)
            if run and run["status"] in {"paused", "cancelled"}:
                self.emit_run(run_id, {"stage": run["status"]})
                return
            ready = self.database.list_queue_items_by_status(run_id, {"ready", "queued"})
            if not ready:
                break
            item = ready[0]
            try:
                self._process_item(run, item, api, headers)
            except Exception as error:
                message = _display_error_message(error)
                self.database.update_queue_item(item["id"], status="failed", error=message)
                stage = "lossy_available" if isinstance(error, LossyAudioAvailable) else "error"
                self.emit_run(
                    run_id,
                    {"stage": stage, "item_id": item["id"], "track_id": item.get("track_id"), "message": message},
                )
        final_status = "complete"
        self.database.update_run(run_id, status=final_status, completed_at=time.time())
        self.emit_run(run_id, {"stage": final_status})

    def _process_item(self, run: dict, item: dict, api: TidalApi, headers: dict[str, str]) -> None:
        run_id = run["id"]
        track = track_from_item(item)
        options = run["options"]
        self.database.update_queue_item(item["id"], status="downloading", error=None)
        self.emit_run(
            run_id,
            {"stage": "downloading", "item_id": item["id"], "track_id": track.track_id, "title": track.title, "artist": track.artist},
        )
        lyrics = ""
        if options.get("embed_lyrics", True) or options.get("write_lrc", False):
            try:
                if hasattr(api, "get_lyrics_payload"):
                    lyrics_payload = api.get_lyrics_payload(track.track_id)
                    lyrics = extract_lyrics_text(lyrics_payload, mode=options.get("lyrics_mode", "auto"))
                else:
                    lyrics = api.get_lyrics(track.track_id)
            except Exception as error:
                self.emit_run(run_id, {"stage": "lyrics_unavailable", "item_id": item["id"], "message": str(error)})
        manifest = self._playback_manifest(
            api,
            track.track_id,
            options.get("audio_quality", "max"),
            allow_lossy_audio=bool(options.get("allow_lossy_audio", False)),
        )

        def emit_download(event: dict) -> None:
            if event.get("stage") == "segment":
                self.database.update_queue_item(
                    item["id"],
                    progress_current=event.get("current", 0),
                    progress_total=event.get("total", 0),
                )
                self.emit_run(
                    run_id,
                    {
                        "stage": "progress",
                        "item_id": item["id"],
                        "track_id": track.track_id,
                        "current": event.get("current", 0),
                        "total": event.get("total", 0),
                    },
                )
            else:
                self.emit_run(run_id, {"item_id": item["id"], **event})

        result = self.downloader(
            track,
            manifest,
            DownloadOptions(
                output_dir=Path(run["output_dir"]),
                concurrency=int(options.get("concurrency") or 10),
                skip_existing=bool(options.get("skip_existing", True)),
                existing_strategy=options.get("existing_strategy") or "skip",
                album_template=options.get("album_template") or "{album_artist}/{album} ({year})",
                filename_template=options.get("filename_template") or "{track_number}. {artist} - {title}",
                single_filename_template=options.get("single_filename_template") or "{artist} - {title}",
                allow_lossy_audio=bool(options.get("allow_lossy_audio", False)),
            ),
            headers,
            emit_download,
        )
        status = "skipped" if result.status == "skipped" else "postprocessing"
        self.database.update_queue_item(item["id"], status=status, output_path=str(result.output_path))
        is_flac_output = result.output_path.suffix.lower() == ".flac"
        is_mp4_output = result.output_path.suffix.lower() in {".m4a", ".mp4"}
        if is_flac_output and options.get("embed_covers", True) and result.status != "skipped":
            self._warn_if_fails(
                run_id,
                item["id"],
                "cover",
                lambda: embed_cover(result.output_path, track.cover_id, Path(run["output_dir"]) / ".covers")
                if not has_cover(result.output_path)
                else True,
            )
            self.emit_run(run_id, {"stage": "cover", "item_id": item["id"], "track_id": track.track_id})
        if is_flac_output and options.get("embed_lyrics", True) and lyrics and result.status != "skipped":
            if self._warn_if_fails(run_id, item["id"], "lyrics", lambda: embed_lyrics(result.output_path, lyrics)):
                self.emit_run(run_id, {"stage": "lyrics", "item_id": item["id"], "track_id": track.track_id})
        if is_mp4_output and options.get("embed_covers", True) and result.status != "skipped":
            if self._warn_if_fails(
                run_id,
                item["id"],
                "cover",
                lambda: embed_mp4_cover(result.output_path, track.cover_id, Path(run["output_dir"]) / ".covers"),
            ):
                self.emit_run(run_id, {"stage": "cover", "item_id": item["id"], "track_id": track.track_id})
        if is_mp4_output and options.get("embed_lyrics", True) and lyrics and result.status != "skipped":
            if self._warn_if_fails(run_id, item["id"], "lyrics", lambda: embed_mp4_lyrics(result.output_path, lyrics)):
                self.emit_run(run_id, {"stage": "lyrics", "item_id": item["id"], "track_id": track.track_id})
        if options.get("write_lrc", False) and lyrics and result.status != "skipped":
            if self._warn_if_fails(run_id, item["id"], "lrc", lambda: write_lrc(result.output_path, lyrics)):
                self.emit_run(run_id, {"stage": "lrc", "item_id": item["id"], "track_id": track.track_id})
        if is_flac_output and result.status != "skipped":
            self._warn_if_fails(run_id, item["id"], "metadata", lambda: repair_flac_tags(result.output_path, track))
        if is_mp4_output and result.status != "skipped":
            self._warn_if_fails(run_id, item["id"], "metadata", lambda: repair_mp4_tags(result.output_path, track))
        final_status = "skipped" if result.status == "skipped" else "complete"
        self.database.update_queue_item(
            item["id"],
            status=final_status,
            output_path=str(result.output_path),
        )
        self.emit_run(
            run_id,
            {
                "stage": "downloaded" if final_status == "complete" else "skipped",
                "item_id": item["id"],
                "track_id": track.track_id,
                "path": str(result.output_path),
                "title": track.title,
                "artist": track.artist,
            },
        )

    def _warn_if_fails(self, run_id: str, item_id: str, stage: str, action: Callable[[], object]) -> object:
        try:
            return action()
        except Exception as error:
            self.emit_run(run_id, {"stage": "warning", "item_id": item_id, "kind": stage, "message": str(error)})
            return False

    def _playback_manifest(self, api: TidalApi, track_id: str, audio_quality: str, allow_lossy_audio: bool = False):
        qualities = ["LOSSLESS", "HIGH"] if audio_quality == "high" else ["HI_RES", "LOSSLESS"]
        errors = []
        lossy_error = None
        unauthorized_qualities = []
        for quality in qualities:
            try:
                playback = api.get(
                    f"tracks/{track_id}/playbackinfopostpaywall",
                    {
                        "audioquality": quality,
                        "playbackmode": "STREAM",
                        "assetpresentation": "FULL",
                    },
                )
                if allow_lossy_audio:
                    return parse_flac_dash_manifest(playback["manifest"], allow_lossy_audio=True)
                return parse_flac_dash_manifest(playback["manifest"])
            except LossyAudioAvailable as error:
                lossy_error = error
                errors.append(f"{quality}: {error}")
            except requests.HTTPError as error:
                if getattr(error.response, "status_code", None) == 401 and quality != qualities[-1]:
                    unauthorized_qualities.append(quality)
                    errors.append(f"{quality}: unavailable")
                    continue
                if getattr(error.response, "status_code", None) == 401:
                    unauthorized_qualities.append(quality)
                errors.append(f"{quality}: {error}")
            except Exception as error:
                errors.append(f"{quality}: {error}")
        if lossy_error:
            raise LossyAudioAvailable(str(lossy_error))
        if len(unauthorized_qualities) == len(qualities):
            raise RuntimeError("该歌曲没有开放给当前账号/地区/版本，请更换歌曲下载。")
        raise RuntimeError("No FLAC playback manifest available. " + " | ".join(errors))

    def pause_run(self, run_id: str) -> dict | None:
        run = self.database.update_run(run_id, status="paused")
        self.emit_run(run_id, {"stage": "paused"})
        return run

    def resume_run(self, run_id: str) -> dict | None:
        run = self.database.update_run(run_id, status="queued")
        self.emit_run(run_id, {"stage": "resumed"})
        self.start_run(run_id)
        return run

    def cancel_run(self, run_id: str) -> dict | None:
        self.database.cancel_queued_items(run_id)
        run = self.database.update_run(run_id, status="cancelled", completed_at=time.time())
        self.emit_run(run_id, {"stage": "cancelled"})
        return run

    def retry_item(self, item_id: str) -> dict | None:
        item = self.database.retry_queue_item(item_id)
        if item:
            run = self.database.get_run(item["run_id"])
            if run and run["status"] in {"complete", "failed", "paused"}:
                self.database.update_run(item["run_id"], status="queued", completed_at=None)
            self._reset_run_stream(item["run_id"])
            self.emit_run(item["run_id"], {"stage": "retried", "item_id": item_id})
            self.start_run(item["run_id"])
        return item

    def retry_item_with_options(self, item_id: str, **option_updates) -> dict | None:
        item = self.database.retry_queue_item(item_id)
        if item:
            run = self.database.get_run(item["run_id"])
            if run:
                options = dict(run.get("options") or {})
                options.update(option_updates)
                self.database.update_run(item["run_id"], status="queued", completed_at=None, options=options)
            self._reset_run_stream(item["run_id"])
            self.emit_run(item["run_id"], {"stage": "retried", "item_id": item_id})
            self.start_run(item["run_id"])
        return item

    def _reset_run_stream(self, run_id: str) -> None:
        with self.lock:
            self.run_events[run_id] = []
            self.run_queues[run_id] = Queue()


def track_to_dict(track: TrackItem) -> dict:
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
    }


def track_from_item(item: dict) -> TrackItem:
    return TrackItem(
        track_id=str(item["track_id"]),
        title=str(item.get("title") or item["track_id"]),
        artist=str(item.get("artist") or "Unknown Artist"),
        album_title=str(item.get("album_title") or ""),
        album_artist=str(item.get("album_artist") or item.get("artist") or "Unknown Artist"),
        album_year=str(item.get("album_year") or ""),
        cover_id=item.get("cover_id"),
        track_number=item.get("track_number"),
        duration_seconds=item.get("duration_seconds"),
        total_tracks=item.get("total_tracks"),
        disc_number=item.get("disc_number"),
        total_discs=item.get("total_discs"),
    )


def _display_error_message(error: Exception) -> str:
    status_code = getattr(getattr(error, "response", None), "status_code", None)
    raw = str(error)
    if status_code == 401 or ("401" in raw and "Unauthorized" in raw):
        return "402, Tidal 授权已失效，请重新绑定账号。"
    return raw


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"
