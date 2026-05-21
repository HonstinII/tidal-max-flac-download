import re
from dataclasses import dataclass

import requests

from .tidal_config import TidalAuthState

BASE_URL = "https://api.tidalhifi.com/v1"
LYRICS_URL = "https://api.tidal.com/v1"
TIDAL_URL_RE = re.compile(r"tidal\.com/(album|track)/(\d+)")


@dataclass(frozen=True)
class TidalReference:
    kind: str
    item_id: str


@dataclass(frozen=True)
class TrackItem:
    track_id: str
    title: str
    artist: str
    album_title: str
    album_artist: str
    album_year: str
    cover_id: str | None
    track_number: int | None = None


def parse_tidal_url(url: str) -> TidalReference:
    match = TIDAL_URL_RE.search(url)
    if not match:
        raise ValueError(f"Unsupported Tidal URL: {url}")
    return TidalReference(kind=match.group(1), item_id=match.group(2))


class TidalApi:
    def __init__(self, auth: TidalAuthState, session=None):
        if not auth.access_token:
            raise ValueError("Tidal access token is required.")
        if not auth.country_code:
            raise ValueError("Tidal country code is required.")
        self.auth = auth
        self.session = session or requests.Session()

    def resolve(self, ref: TidalReference) -> list[TrackItem]:
        if ref.kind == "track":
            track = self.get(f"tracks/{ref.item_id}")
            return [self._track_item(track, None, None)]
        if ref.kind == "album":
            album = self.get(f"albums/{ref.item_id}")
            items = self.get(f"albums/{ref.item_id}/items").get("items", [])
            return [
                self._track_item(item["item"], album, index)
                for index, item in enumerate(items, 1)
            ]
        raise ValueError(f"Unsupported Tidal reference: {ref.kind}")

    def get(self, path: str, params=None) -> dict:
        merged_params = dict(params or {})
        merged_params.setdefault("countryCode", self.auth.country_code)
        merged_params.setdefault("limit", 100)
        response = self.session.get(
            f"{BASE_URL}/{path}",
            headers={"authorization": f"Bearer {self.auth.access_token}"},
            params=merged_params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_lyrics(self, track_id: str) -> str:
        from .lyrics import extract_lyrics_text

        return extract_lyrics_text(self.get_lyrics_payload(track_id))

    def get_lyrics_payload(self, track_id: str) -> dict:
        response = self.session.get(
            f"{LYRICS_URL}/tracks/{track_id}/lyrics",
            headers={"authorization": f"Bearer {self.auth.access_token}"},
            params={"countryCode": self.auth.country_code, "limit": 100},
            timeout=30,
        )
        if response.status_code in {401, 404}:
            return {}
        response.raise_for_status()
        return response.json()

    def _track_item(
        self, track: dict, album: dict | None, track_number: int | None
    ) -> TrackItem:
        track_album = album or track.get("album") or {}
        album_artist = track_album.get("artist", {}).get("name") or track.get(
            "artist", {}
        ).get("name", "Unknown Artist")
        return TrackItem(
            track_id=str(track["id"]),
            title=str(track.get("title") or track["id"]),
            artist=str(track.get("artist", {}).get("name") or "Unknown Artist"),
            album_title=str(track_album.get("title") or track.get("title") or ""),
            album_artist=str(album_artist),
            album_year=str(
                (track_album.get("releaseDate") or track.get("streamStartDate") or "")[
                    :4
                ]
            ),
            cover_id=track_album.get("cover"),
            track_number=track_number,
        )
