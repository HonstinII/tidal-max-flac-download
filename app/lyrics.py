from pathlib import Path
import subprocess

from mutagen.flac import FLAC


def extract_lyrics_text(payload: dict, mode: str = "auto") -> str:
    if mode == "synced":
        lyrics = str(payload.get("subtitles") or "").strip()
    elif mode == "plain":
        lyrics = str(payload.get("lyrics") or "").strip()
    else:
        lyrics = str(payload.get("subtitles") or payload.get("lyrics") or "").strip()
    return "" if is_placeholder_lyrics(lyrics) else lyrics


def is_placeholder_lyrics(lyrics: str) -> bool:
    text = "".join(char for char in lyrics if not char.isspace())
    if not text:
        return False
    hash_count = text.count("#")
    return hash_count >= 12 and hash_count / len(text) > 0.55


def build_set_lyrics_command(flac_path: Path, lyrics: str) -> list[str]:
    return [
        "metaflac",
        f"--set-tag=LYRICS={lyrics}",
        str(flac_path),
    ]


def embed_lyrics(flac_path: Path, lyrics: str | None) -> bool:
    if not lyrics:
        return False
    audio = FLAC(str(flac_path))
    audio["LYRICS"] = lyrics
    audio.save()
    return True


def write_lrc(flac_path: Path, lyrics: str | None) -> Path | None:
    if not lyrics:
        return None
    lrc_path = flac_path.with_suffix(".lrc")
    lrc_path.write_text(lyrics.rstrip() + "\n", encoding="utf-8")
    return lrc_path
