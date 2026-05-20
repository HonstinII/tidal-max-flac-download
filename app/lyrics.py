from pathlib import Path
import subprocess


def extract_lyrics_text(payload: dict) -> str:
    return str(payload.get("subtitles") or payload.get("lyrics") or "").strip()


def build_set_lyrics_command(flac_path: Path, lyrics: str) -> list[str]:
    return [
        "metaflac",
        "--remove-tag=LYRICS",
        f"--set-tag=LYRICS={lyrics}",
        str(flac_path),
    ]


def embed_lyrics(flac_path: Path, lyrics: str | None) -> bool:
    if not lyrics:
        return False
    subprocess.run(build_set_lyrics_command(flac_path, lyrics), check=True)
    return True
