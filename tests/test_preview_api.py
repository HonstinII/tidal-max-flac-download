from fastapi.testclient import TestClient

from app.main import app
from app.tidal_api import TrackItem


class Auth:
    access_token = "token"
    country_code = "US"


def track_item(track_id="1", title="Song", track_number=1):
    return TrackItem(
        track_id=track_id,
        title=title,
        artist="Artist",
        album_title="Album",
        album_artist="Album Artist",
        album_year="2024",
        cover_id="cover-id",
        track_number=track_number,
    )


def test_preview_track_url_returns_track(monkeypatch):
    class FakeApi:
        def __init__(self, auth):
            pass

        def resolve(self, ref):
            assert ref.kind == "track"
            return [track_item()]

    monkeypatch.setattr("app.main.read_tidal_auth", lambda path: Auth())
    monkeypatch.setattr("app.main.TidalApi", FakeApi)

    client = TestClient(app)
    response = client.post("/api/preview", json={"urls": ["https://tidal.com/track/1/u"]})

    assert response.status_code == 200
    data = response.json()
    assert data["errors"] == []
    assert data["items"][0]["kind"] == "track"
    assert data["items"][0]["track_count"] == 1
    assert data["items"][0]["tracks"][0]["title"] == "Song"


def test_preview_album_url_returns_album_tracks(monkeypatch):
    class FakeApi:
        def __init__(self, auth):
            pass

        def resolve(self, ref):
            assert ref.kind == "album"
            return [track_item("1", "One", 1), track_item("2", "Two", 2)]

    monkeypatch.setattr("app.main.read_tidal_auth", lambda path: Auth())
    monkeypatch.setattr("app.main.TidalApi", FakeApi)

    client = TestClient(app)
    response = client.post("/api/preview", json={"urls": ["https://tidal.com/album/9/u"]})

    data = response.json()
    assert data["items"][0]["kind"] == "album"
    assert data["items"][0]["track_count"] == 2
    assert data["items"][0]["album_title"] == "Album"
    assert [track["title"] for track in data["items"][0]["tracks"]] == ["One", "Two"]


def test_preview_invalid_url_returns_error(monkeypatch):
    monkeypatch.setattr("app.main.read_tidal_auth", lambda path: Auth())

    client = TestClient(app)
    response = client.post("/api/preview", json={"urls": ["https://example.com/nope"]})

    data = response.json()
    assert data["items"] == []
    assert data["errors"][0]["url"] == "https://example.com/nope"
    assert "Unsupported Tidal URL" in data["errors"][0]["message"]
