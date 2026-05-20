from fastapi.testclient import TestClient

from app.installer import InstallJobManager
from app.main import app


def test_install_missing_tools_api_streams_command_events(monkeypatch):
    calls = []

    def fake_setup_status():
        return {
            "tools": {"streamrip": True, "ffmpeg": False, "metaflac": False},
            "streamrip_config": {"path": "/tmp/config.toml", "exists": True},
            "output_dir": "/tmp/music",
            "tidal": {"bound": False},
        }

    def runner(command, on_line):
        calls.append(command)
        on_line("fake install ok")
        return 0

    monkeypatch.setattr("app.main.setup_status", fake_setup_status)
    monkeypatch.setattr(
        "app.main.install_manager",
        InstallJobManager(runner=runner, platform_name="Darwin"),
    )

    client = TestClient(app)
    response = client.post("/api/tools/install")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    events = client.get(f"/api/tools/install/{job_id}/events").text

    assert calls == [["brew", "install", "ffmpeg", "flac"]]
    assert "brew install ffmpeg flac" in events
    assert "fake install ok" in events
    assert "complete" in events
