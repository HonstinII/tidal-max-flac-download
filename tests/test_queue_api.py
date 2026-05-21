from fastapi.testclient import TestClient

from app.main import app
from app.storage import AppDatabase
from app.tidal_api import TrackItem


class Auth:
    access_token = "token"
    country_code = "US"


def make_track(track_id="1", title="Song"):
    return TrackItem(
        track_id=track_id,
        title=title,
        artist="Artist",
        album_title="Album",
        album_artist="Album Artist",
        album_year="2024",
        cover_id="cover-id",
        track_number=1,
    )


def test_queue_api_creates_run_and_items(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()

    class FakeApi:
        def __init__(self, auth):
            pass

        def resolve(self, ref):
            return [make_track()]

    monkeypatch.setattr("app.main.database", db)
    monkeypatch.setattr("app.main.read_tidal_auth", lambda path: Auth())
    monkeypatch.setattr("app.main.TidalApi", FakeApi)

    client = TestClient(app)
    response = client.post(
        "/api/queue",
        json={
            "urls": ["https://tidal.com/track/1/u"],
            "output_dir": "/tmp/music",
            "concurrency": 4,
            "embed_covers": True,
            "embed_lyrics": True,
            "existing_strategy": "skip",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["run"]["status"] == "queued"
    assert data["items"][0]["title"] == "Song"
    assert data["items"][0]["status"] == "ready"
    assert data["items"][0]["progress_current"] == 0


def test_queue_api_lists_items(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()
    db.create_run("run-1", "queued", "/tmp/music", {})
    db.create_queue_item(
        "item-1",
        "run-1",
        "https://tidal.com/track/1/u",
        make_track().__dict__,
        status="ready",
    )
    monkeypatch.setattr("app.main.database", db)

    client = TestClient(app)
    response = client.get("/api/queue")

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["id"] == "item-1"
    assert data["items"][0]["artist"] == "Artist"
