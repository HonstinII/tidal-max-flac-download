from pathlib import Path
import subprocess

import requests


def build_cover_url(cover_id: str, size: int = 1280) -> str:
    return (
        f"https://resources.tidal.com/images/"
        f"{cover_id.replace('-', '/')}/{size}x{size}.jpg"
    )


def build_metaflac_command(flac_path: Path, image_path: Path) -> list[str]:
    return [
        "metaflac",
        f"--import-picture-from=3|image/jpeg|||{image_path}",
        str(flac_path),
    ]


def download_cover(cover_id: str, cache_dir: Path, size: int = 1280) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    image_path = cache_dir / f"{cover_id}-{size}.jpg"
    if image_path.exists():
        return image_path

    response = requests.get(build_cover_url(cover_id, size), timeout=30)
    response.raise_for_status()
    image_path.write_bytes(response.content)
    return image_path


def embed_cover(flac_path: Path, cover_id: str | None, cache_dir: Path) -> bool:
    if not cover_id:
        return False
    image_path = download_cover(cover_id, cache_dir)
    subprocess.run(
        ["metaflac", "--remove", "--block-type=PICTURE", str(flac_path)],
        check=True,
    )
    subprocess.run(build_metaflac_command(flac_path, image_path), check=True)
    return True
