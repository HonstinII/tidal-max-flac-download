import base64
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, Literal

import requests

from .tidal_api import TrackItem


class NoFlacRepresentation(RuntimeError):
    pass


@dataclass(frozen=True)
class FlacDashManifest:
    initialization_url: str
    segment_urls: list[str]
    codec: str
    sample_rate: str | None


@dataclass(frozen=True)
class DownloadOptions:
    output_dir: Path
    concurrency: int = 10
    skip_existing: bool = True
    existing_strategy: Literal["skip", "overwrite", "keep_both"] | None = None


@dataclass(frozen=True)
class DownloadResult:
    track_id: str
    output_path: Path
    status: str


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:180] or "untitled"


def parse_flac_dash_manifest(manifest_b64: str) -> FlacDashManifest:
    xml = base64.b64decode(manifest_b64).decode("utf-8")
    root = ET.fromstring(xml)
    ns = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}
    rep = root.find(".//mpd:Representation", ns)
    template = root.find(".//mpd:SegmentTemplate", ns)
    timeline = root.findall(".//mpd:SegmentTimeline/mpd:S", ns)
    if rep is None or template is None:
        raise NoFlacRepresentation("Missing DASH FLAC representation.")

    codec = rep.attrib.get("codecs", "")
    if codec.lower() != "flac":
        raise NoFlacRepresentation(f"Expected FLAC representation, got {codec!r}.")

    start = int(template.attrib.get("startNumber", "1"))
    count = sum(int(item.attrib.get("r", "0")) + 1 for item in timeline)
    media = template.attrib["media"]
    return FlacDashManifest(
        initialization_url=template.attrib["initialization"],
        segment_urls=[
            media.replace("$Number$", str(number))
            for number in range(start, start + count)
        ],
        codec=codec,
        sample_rate=rep.attrib.get("audioSamplingRate"),
    )


def build_output_path(track: TrackItem, output_dir: Path) -> Path:
    if track.track_number is not None:
        folder = safe_name(
            f"{track.album_artist} - {track.album_title} ({track.album_year})"
        )
        prefix = f"{track.track_number:02d}. "
        return output_dir / folder / f"{prefix}{safe_name(track.artist)} - {safe_name(track.title)}.flac"
    return output_dir / f"{safe_name(track.artist)} - {safe_name(track.title)}.flac"


def prepare_output_path(output: Path, options: DownloadOptions) -> tuple[Path, str]:
    strategy = options.existing_strategy
    if strategy is None:
        strategy = "skip" if options.skip_existing else "overwrite"
    if not output.exists():
        return output, "download"
    if strategy == "skip" and output.stat().st_size > 1024 * 1024:
        return output, "skipped"
    if strategy == "overwrite":
        return output, "download"
    if strategy == "keep_both":
        index = 2
        while True:
            candidate = output.with_name(f"{output.stem} ({index}){output.suffix}")
            if not candidate.exists():
                return candidate, "download"
            index += 1
    return output, "download"


def download_track_as_flac(
    track: TrackItem,
    manifest: FlacDashManifest,
    options: DownloadOptions,
    headers: dict[str, str],
    emit: Callable[[dict], None] | None = None,
) -> DownloadResult:
    emit = emit or (lambda event: None)
    output = build_output_path(track, options.output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output, output_status = prepare_output_path(output, options)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_status == "skipped":
        emit(
            {
                "stage": "skipped",
                "track_id": track.track_id,
                "path": str(output),
                "title": track.title,
                "artist": track.artist,
            }
        )
        return DownloadResult(track.track_id, output, "skipped")

    emit({"stage": "downloading", "track_id": track.track_id, "title": track.title, "artist": track.artist})
    with tempfile.TemporaryDirectory(prefix="tidal-max-") as tmp:
        tmp_path = Path(tmp)
        urls = list(enumerate([manifest.initialization_url, *manifest.segment_urls]))
        total_parts = len(urls)
        parts = []
        with ThreadPoolExecutor(max_workers=max(1, options.concurrency)) as executor:
            futures = [
                executor.submit(_fetch_part, tmp_path, headers, item) for item in urls
            ]
            for future in as_completed(futures):
                parts.append(future.result())
                emit(
                    {
                        "stage": "segment",
                        "track_id": track.track_id,
                        "current": len(parts),
                        "total": total_parts,
                    }
                )
        parts.sort()

        joined = tmp_path / "joined.mp4"
        with joined.open("wb") as handle:
            for part in parts:
                handle.write(part.read_bytes())

        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(joined),
            "-map",
            "0:a:0",
            "-c:a",
            "flac",
            "-metadata",
            f"title={track.title}",
            "-metadata",
            f"artist={track.artist}",
            "-metadata",
            f"album={track.album_title}",
            str(output),
        ]
        if track.track_number is not None:
            cmd[-1:-1] = ["-metadata", f"track={track.track_number}"]
        if track.album_year:
            cmd[-1:-1] = ["-metadata", f"date={track.album_year}"]
        subprocess.run(cmd, check=True)

    emit({"stage": "downloaded", "track_id": track.track_id, "path": str(output), "title": track.title, "artist": track.artist})
    return DownloadResult(track.track_id, output, "complete")


def _fetch_part(tmp_path: Path, headers: dict[str, str], index_and_url: tuple[int, str]):
    index, url = index_and_url
    part = tmp_path / f"{index:05d}.mp4"
    last_error = None
    for _ in range(3):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                with part.open("wb") as handle:
                    shutil.copyfileobj(response.raw, handle)
            return part
        except requests.RequestException as error:
            last_error = error
    raise RuntimeError(f"Failed to download segment: {last_error}")
