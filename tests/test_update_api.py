from fastapi.testclient import TestClient

from app.main import app


def test_update_check_api_returns_update_info(monkeypatch):
    monkeypatch.setattr(
        "app.main.check_for_update",
        lambda: {
            "current_version": "0.3.8",
            "latest_version": "v0.3.9",
            "available": True,
            "release_url": "https://example.test/release",
            "release_notes": "notes",
            "asset_name": "Tidal-Max-FLAC-Studio-macOS.zip",
            "asset_url": "https://example.test/mac.zip",
        },
    )

    client = TestClient(app)
    response = client.get("/api/update/check")

    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["asset_name"] == "Tidal-Max-FLAC-Studio-macOS.zip"


def test_update_download_api_downloads_and_opens_folder(monkeypatch, tmp_path):
    downloaded = tmp_path / "Tidal-Max-FLAC-Studio-macOS.zip"
    opened = []
    monkeypatch.setattr("app.main.download_update_asset", lambda *args: downloaded)
    monkeypatch.setattr("app.main.open_folder", lambda path: opened.append(path))

    client = TestClient(app)
    response = client.post(
        "/api/update/download",
        json={
            "asset_url": "https://example.test/mac.zip",
            "asset_name": "Tidal-Max-FLAC-Studio-macOS.zip",
        },
    )

    assert response.status_code == 200
    assert response.json()["path"] == str(downloaded)
    assert opened == [tmp_path]
