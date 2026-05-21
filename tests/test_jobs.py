from app.jobs import DownloadJobManager, JobOptions
from app.downloader import DownloadResult
from app.storage import AppDatabase
from app.tidal_api import TrackItem


class Auth:
    access_token = "token"
    country_code = "US"


class FakeApi:
    def __init__(self, auth):
        pass

    def resolve(self, ref):
        return [
            TrackItem(
                track_id="1",
                title="Song",
                artist="Artist",
                album_title="Album",
                album_artist="Album Artist",
                album_year="2024",
                cover_id=None,
                track_number=1,
            )
        ]

    def get_lyrics(self, track_id):
        return ""

    def get_lyrics_payload(self, track_id):
        return {"subtitles": "[00:01.00] synced", "lyrics": "plain"}

    def get(self, path, params=None):
        return {"manifest": "unused"}


def test_create_job_stores_urls_and_options():
    manager = DownloadJobManager()

    job = manager.create_job(["https://tidal.com/track/1"], JobOptions(concurrency=4))

    assert job.job_id
    assert job.urls == ["https://tidal.com/track/1"]
    assert job.options.concurrency == 4
    assert manager.get_job(job.job_id) == job


def test_job_records_events_in_order():
    manager = DownloadJobManager()
    job = manager.create_job(["url"], JobOptions())

    manager.emit(job.job_id, {"stage": "one"})
    manager.emit(job.job_id, {"stage": "two"})

    assert [event["stage"] for event in manager.get_job(job.job_id).events] == [
        "created",
        "one",
        "two",
    ]


def test_queue_worker_updates_item_progress_and_completion(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()

    def fake_downloader(track, manifest, options, headers, emit):
        emit({"stage": "segment", "track_id": track.track_id, "current": 1, "total": 2})
        emit({"stage": "segment", "track_id": track.track_id, "current": 2, "total": 2})
        output = tmp_path / "Song.flac"
        output.write_text("audio")
        return DownloadResult(track.track_id, output, "complete")

    monkeypatch.setattr("app.jobs.parse_flac_dash_manifest", lambda manifest: manifest)
    monkeypatch.setattr("app.jobs.embed_cover", lambda *args, **kwargs: False)
    manager = DownloadJobManager(
        database=db,
        auth_reader=lambda path: Auth(),
        api_factory=FakeApi,
        downloader=fake_downloader,
    )
    run = manager.create_run_from_urls(
        ["https://tidal.com/track/1"],
        JobOptions(output_dir=tmp_path, embed_covers=False, embed_lyrics=False),
    )

    manager._run_queue(run["id"])

    item = db.list_queue_items(run["id"])[0]
    assert item["status"] == "complete"
    assert item["progress_current"] == 2
    assert item["progress_total"] == 2
    assert item["output_path"] == str(tmp_path / "Song.flac")
    assert db.get_run(run["id"])["status"] == "complete"
    assert any(event["stage"] == "downloaded" for event in manager.run_events[run["id"]])


def test_queue_worker_runs_metadata_postprocessing(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()
    calls = []

    def fake_downloader(track, manifest, options, headers, emit):
        calls.append(("templates", options.album_template, options.filename_template, options.single_filename_template))
        output = tmp_path / "Song.flac"
        output.write_text("audio")
        return DownloadResult(track.track_id, output, "complete")

    monkeypatch.setattr("app.jobs.parse_flac_dash_manifest", lambda manifest: manifest)
    monkeypatch.setattr("app.jobs.embed_cover", lambda *args, **kwargs: calls.append(("cover", args[0])) or True)
    monkeypatch.setattr("app.jobs.embed_lyrics", lambda *args, **kwargs: calls.append(("lyrics", args[1])) or True)
    monkeypatch.setattr("app.jobs.write_lrc", lambda *args, **kwargs: calls.append(("lrc", args[1])) or (tmp_path / "Song.lrc"))
    monkeypatch.setattr("app.jobs.repair_flac_tags", lambda *args, **kwargs: calls.append(("repair", args[1].title)) or True)
    monkeypatch.setattr("app.jobs.has_cover", lambda *args, **kwargs: False)
    manager = DownloadJobManager(
        database=db,
        auth_reader=lambda path: Auth(),
        api_factory=FakeApi,
        downloader=fake_downloader,
    )
    run = manager.create_run_from_urls(
        ["https://tidal.com/track/1"],
        JobOptions(
            output_dir=tmp_path,
            embed_covers=True,
            embed_lyrics=True,
            write_lrc=True,
            lyrics_mode="synced",
            album_template="{album_artist}/{album} ({year})",
            filename_template="{track_number}. {artist} - {title}",
            single_filename_template="{artist} - {title}",
        ),
    )

    manager._run_queue(run["id"])

    assert ("templates", "{album_artist}/{album} ({year})", "{track_number}. {artist} - {title}", "{artist} - {title}") in calls
    assert ("cover", tmp_path / "Song.flac") in calls
    assert ("lyrics", "[00:01.00] synced") in calls
    assert ("lrc", "[00:01.00] synced") in calls
    assert ("repair", "Song") in calls


def test_queue_worker_marks_single_item_failed_and_completes_run(monkeypatch, tmp_path):
    db = AppDatabase(tmp_path / "queue.db")
    db.initialize()

    def failing_downloader(track, manifest, options, headers, emit):
        raise RuntimeError("download exploded")

    monkeypatch.setattr("app.jobs.parse_flac_dash_manifest", lambda manifest: manifest)
    manager = DownloadJobManager(
        database=db,
        auth_reader=lambda path: Auth(),
        api_factory=FakeApi,
        downloader=failing_downloader,
    )
    run = manager.create_run_from_urls(
        ["https://tidal.com/track/1"],
        JobOptions(output_dir=tmp_path, embed_covers=False, embed_lyrics=False),
    )

    manager._run_queue(run["id"])

    item = db.list_queue_items(run["id"])[0]
    assert item["status"] == "failed"
    assert "download exploded" in item["error"]
    assert db.get_run(run["id"])["status"] == "complete"
