from fastapi.testclient import TestClient

from app.installer import InstallJobManager
from app.main import app


def test_install_missing_tools_api_streams_command_events(monkeypatch):
    calls = []

    def fake_setup_status():
        return {
            "tools": {"streamrip": True, "ffmpeg": False, "metaflac": False},
            "platform": {"system": "Darwin", "name": "macOS", "supports_auto_install": True},
            "tools_detail": {
                "streamrip": {"ok": True},
                "ffmpeg": {"ok": False},
                "metaflac": {"ok": False},
            },
            "package_managers": {"homebrew": {"ok": True}, "winget": {"ok": False}},
            "manual_commands": {
                "streamrip": "python3 -m pip install --user streamrip",
                "ffmpeg": "brew install ffmpeg",
                "metaflac": "brew install flac",
            },
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

    assert calls == [["brew", "install", "ffmpeg"], ["brew", "install", "flac"]]
    assert "step_started" in events
    assert "brew install ffmpeg" in events
    assert "fake install ok" in events
    assert "complete" in events


def test_bundled_flac_endpoint_returns_missing_message(monkeypatch, tmp_path):
    monkeypatch.setattr("app.main.extract_bundled_flac", lambda: {"ok": False, "message": "missing", "target": str(tmp_path)})

    client = TestClient(app)
    response = client.post("/api/tools/bundled-flac")

    assert response.status_code == 200
    assert response.json()["ok"] is False
