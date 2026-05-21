from pathlib import Path

from mutagen.flac import FLAC
from mutagen.mp4 import MP4

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
        audio["album artist"] = [track.album_artist]
    if track.album_year:
        audio["date"] = [track.album_year]
    if track.track_number is not None:
        audio["tracknumber"] = [str(track.track_number)]
    if track.total_tracks is not None:
        audio["tracktotal"] = [str(track.total_tracks)]
        audio["totaltracks"] = [str(track.total_tracks)]
    if track.disc_number is not None:
        audio["discnumber"] = [str(track.disc_number)]
    if track.total_discs is not None:
        audio["disctotal"] = [str(track.total_discs)]
        audio["totaldiscs"] = [str(track.total_discs)]
    audio.save()
    return True


def repair_mp4_tags(mp4_path: Path, track: TrackItem) -> bool:
    audio = MP4(str(mp4_path))
    audio["\xa9nam"] = [track.title or str(track.track_id)]
    audio["\xa9ART"] = [track.artist or "Unknown Artist"]
    if track.album_title:
        audio["\xa9alb"] = [track.album_title]
    if track.album_artist:
        audio["aART"] = [track.album_artist]
    if track.album_year:
        audio["\xa9day"] = [track.album_year]
    if track.track_number is not None:
        audio["trkn"] = [(track.track_number, track.total_tracks or 0)]
    if track.disc_number is not None:
        audio["disk"] = [(track.disc_number, track.total_discs or 0)]
    audio.save()
    return True
