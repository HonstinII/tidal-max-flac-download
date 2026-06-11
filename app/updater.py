from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import re
import shutil

import requests

from .version import APP_VERSION


RELEASE_API_URL = "https://api.github.com/repos/HonstinII/tidal-max-flac-download/releases/latest"
RELEASES_PAGE_URL = "https://github.com/HonstinII/tidal-max-flac-download/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    available: bool
    release_url: str
    release_notes: str
    asset_name: str | None
    asset_url: str | None


def normalize_version(version: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", version)
    return tuple(int(number) for number in numbers[:4]) or (0,)


def is_newer_version(latest: str, current: str) -> bool:
    latest_parts = normalize_version(latest)
    current_parts = normalize_version(current)
    size = max(len(latest_parts), len(current_parts))
    latest_parts = latest_parts + (0,) * (size - len(latest_parts))
    current_parts = current_parts + (0,) * (size - len(current_parts))
    return latest_parts > current_parts


def platform_asset_name(system: str | None = None) -> str | None:
    system = system or platform.system()
    if system == "Darwin":
        return "Tidal-Max-FLAC-Studio-macOS.zip"
    if system == "Windows":
        return "Tidal-Max-FLAC-Studio-Windows.zip"
    return None


def check_for_update(
    current_version: str = APP_VERSION,
    system: str | None = None,
    session=None,
) -> UpdateInfo:
    session = session or requests.Session()
    response = session.get(RELEASE_API_URL, timeout=20)
    response.raise_for_status()
    release = response.json()
    latest_version = str(release.get("tag_name") or "")
    wanted_asset = platform_asset_name(system)
    asset = next(
        (
            item
            for item in release.get("assets", [])
            if item.get("name") == wanted_asset
        ),
        None,
    )
    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        available=is_newer_version(latest_version, current_version),
        release_url=str(release.get("html_url") or RELEASES_PAGE_URL),
        release_notes=str(release.get("body") or ""),
        asset_name=str(asset.get("name")) if asset else wanted_asset,
        asset_url=str(asset.get("browser_download_url")) if asset else None,
    )


def updates_dir() -> Path:
    return Path.home() / "Downloads" / "Tidal Max FLAC Studio Updates"


def download_update_asset(asset_url: str, asset_name: str, target_dir: Path | None = None) -> Path:
    if not asset_url:
        raise ValueError("Update asset URL is required.")
    target_dir = target_dir or updates_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / asset_name
    temporary = target.with_suffix(target.suffix + ".download")
    with requests.get(asset_url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with temporary.open("wb") as handle:
            shutil.copyfileobj(response.raw, handle)
    temporary.replace(target)
    return target
