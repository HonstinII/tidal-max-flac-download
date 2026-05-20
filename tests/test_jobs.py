from app.jobs import DownloadJobManager, JobOptions


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
