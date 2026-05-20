import pytest

from app.tidal_api import TidalApi, parse_tidal_url
from app.tidal_config import TidalAuthState


def test_parse_track_url_with_share_suffix():
    ref = parse_tidal_url("https://tidal.com/track/526130766/u")

    assert ref.kind == "track"
    assert ref.item_id == "526130766"


def test_parse_album_url_with_share_suffix():
    ref = parse_tidal_url("https://tidal.com/album/523643849/u")

    assert ref.kind == "album"
    assert ref.item_id == "523643849"


def test_parse_unsupported_url_fails_clearly():
    with pytest.raises(ValueError, match="Unsupported Tidal URL"):
        parse_tidal_url("https://example.com/nope")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.requests.append({"url": url, "headers": headers, "params": params})
        return FakeResponse(self.payloads.pop(0))


def test_resolve_album_expands_track_items():
    session = FakeSession(
        [
            {
                "id": 9,
                "title": "Album",
                "artist": {"name": "Artist"},
                "releaseDate": "2026-01-02",
                "cover": "cover-id",
            },
            {
                "items": [
                    {"item": {"id": 1, "title": "One", "artist": {"name": "Artist"}}},
                    {"item": {"id": 2, "title": "Two", "artist": {"name": "Artist"}}},
                ]
            },
        ]
    )
    api = TidalApi(
        TidalAuthState(
            bound=True,
            country_code="US",
            access_token="token",
            refresh_token="refresh",
        ),
        session=session,
    )

    tracks = api.resolve(parse_tidal_url("https://tidal.com/album/9"))

    assert [track.track_id for track in tracks] == ["1", "2"]
    assert [track.track_number for track in tracks] == [1, 2]
    assert tracks[0].album_title == "Album"
