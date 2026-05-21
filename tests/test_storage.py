from app.storage import AppDatabase


def test_storage_initializes_schema(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()

    tables = db.table_names()

    assert {"download_runs", "queue_items", "settings"}.issubset(tables)


def test_storage_creates_and_reads_run(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()

    db.create_run(
        run_id="run-1",
        status="queued",
        output_dir="/tmp/music",
        options={"existing_strategy": "skip"},
    )

    run = db.get_run("run-1")
    assert run["id"] == "run-1"
    assert run["status"] == "queued"
    assert run["output_dir"] == "/tmp/music"
    assert run["options"]["existing_strategy"] == "skip"


def test_storage_creates_and_updates_queue_item(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()
    db.create_run("run-1", "queued", "/tmp/music", {})

    db.create_queue_item(
        item_id="item-1",
        run_id="run-1",
        source_url="https://tidal.com/track/1",
        track={
            "track_id": "1",
            "title": "Song",
            "artist": "Artist",
            "album_title": "Album",
            "album_artist": "Album Artist",
            "album_year": "2024",
            "track_number": 2,
            "cover_id": "cover-id",
        },
        status="ready",
    )
    db.update_queue_item(
        "item-1",
        status="downloading",
        progress_current=3,
        progress_total=10,
        output_path="/tmp/music/song.flac",
    )

    item = db.get_queue_item("item-1")
    assert item["status"] == "downloading"
    assert item["title"] == "Song"
    assert item["progress_current"] == 3
    assert item["progress_total"] == 10
    assert item["output_path"] == "/tmp/music/song.flac"
    assert db.list_queue_items("run-1")[0]["id"] == "item-1"


def test_storage_retries_and_cancels_queue_items(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()
    db.create_run("run-1", "queued", "/tmp/music", {})
    db.create_queue_item(
        "failed-1",
        "run-1",
        "https://tidal.com/track/1",
        {"track_id": "1", "title": "Song"},
        status="failed",
    )
    db.update_queue_item("failed-1", error="network", progress_current=5, progress_total=10)

    retried = db.retry_queue_item("failed-1")

    assert retried["status"] == "ready"
    assert retried["attempts"] == 1
    assert retried["error"] is None
    assert retried["progress_current"] == 0

    db.cancel_queued_items("run-1")

    assert db.get_queue_item("failed-1")["status"] == "cancelled"


def test_storage_lists_runs_newest_first(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()
    db.create_run("run-1", "complete", "/tmp/one", {})
    db.create_run("run-2", "queued", "/tmp/two", {})

    assert [run["id"] for run in db.list_runs()] == ["run-2", "run-1"]
