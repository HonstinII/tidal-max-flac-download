from fastapi.testclient import TestClient

from app.jobs import DownloadJobManager
from app.main import app
from app.storage import AppDatabase


def seed_run(db):
    db.initialize()
    db.create_run("run-1", "queued", "/tmp/music", {})
    db.create_queue_item(
        "item-1",
        "run-1",
        "https://tidal.com/track/1",
        {"track_id": "1", "title": "Song", "artist": "Artist"},
        status="failed",
    )
    db.update_queue_item("item-1", error="boom")


def test_retry_failed_item_resets_status(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    seed_run(db)
    manager = DownloadJobManager(database=db)
    started = []

    def fake_start_run(run_id):
        started.append(run_id)

    monkeypatch.setattr(manager, "start_run", fake_start_run)
    monkeypatch.setattr("app.main.database", db)
    monkeypatch.setattr("app.main.job_manager", manager)

    client = TestClient(app)
    response = client.post("/api/queue/items/item-1/retry")

    item = response.json()["item"]
    assert item["status"] == "ready"
    assert item["attempts"] == 1
    assert item["error"] is None
    assert response.json()["run"]["status"] == "queued"
    assert started == ["run-1"]


def test_retry_can_allow_lossy_audio(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    seed_run(db)
    manager = DownloadJobManager(database=db)
    monkeypatch.setattr(manager, "start_run", lambda run_id: None)
    monkeypatch.setattr("app.main.database", db)
    monkeypatch.setattr("app.main.job_manager", manager)

    client = TestClient(app)
    response = client.post("/api/queue/items/item-1/retry", json={"allow_lossy_audio": True})

    assert response.json()["item"]["status"] == "ready"
    assert response.json()["run"]["options"]["allow_lossy_audio"] is True


def test_pause_resume_and_cancel_run(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    seed_run(db)
    monkeypatch.setattr("app.main.database", db)
    monkeypatch.setattr("app.main.job_manager", DownloadJobManager(database=db))

    client = TestClient(app)
    assert client.post("/api/queue/runs/run-1/pause").json()["run"]["status"] == "paused"
    assert client.post("/api/queue/runs/run-1/resume").json()["run"]["status"] == "queued"
    assert client.post("/api/queue/runs/run-1/cancel").json()["run"]["status"] == "cancelled"
    assert db.get_queue_item("item-1")["status"] == "cancelled"
