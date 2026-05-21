from fastapi.testclient import TestClient

from app.main import app
from app.storage import AppDatabase


def test_history_returns_recent_runs(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()
    db.create_run("run-1", "complete", "/tmp/music", {"existing_strategy": "skip"})
    monkeypatch.setattr("app.main.database", db)

    client = TestClient(app)
    response = client.get("/api/history")

    assert response.status_code == 200
    assert response.json()["runs"][0]["id"] == "run-1"


def test_log_export_includes_run_and_track(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()
    db.create_run("run-1", "complete", "/tmp/music", {"existing_strategy": "skip"})
    db.create_queue_item(
        "item-1",
        "run-1",
        "https://tidal.com/track/1",
        {"track_id": "1", "title": "Song", "artist": "Artist"},
        status="complete",
    )
    db.update_queue_item("item-1", output_path="/tmp/music/Song.flac")
    monkeypatch.setattr("app.main.database", db)

    client = TestClient(app)
    response = client.get("/api/logs/run-1.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "Run: run-1" in response.text
    assert "Artist - Song" in response.text
    assert "/tmp/music/Song.flac" in response.text
