from pathlib import Path

from mutagen.flac import FLAC

from .tidal_api import TrackItem


def has_cover(flac_path: Path) -> bool:
    audio = FLAC(str(flac_path))
    return bool(getattr(audio, "pictures", []))


def repair_flac_tags(flac_path: Path, track: TrackItem) -> bool:
    audio = FLAC(str(flac_path))
    audio["title"] = [track.title or str(track.track_id)]
    audio["artist"] = [track.artist or "Unknown Artist"]
    if track.album_title:
        audio["album"] = [track.album_title]
    if track.album_artist:
        audio["albumartist"] = [track.album_artist]
    if track.album_year:
        audio["date"] = [track.album_year]
    if track.track_number is not None:
        audio["tracknumber"] = [str(track.track_number)]
    audio.save()
    return True
