from pathlib import Path

from app.config import cover_cache_dir, default_config, setup_status, streamrip_config_path, tool_status


def test_default_output_directory_uses_music_streamrip():
    config = default_config()

    assert config.output_dir == Path.home() / "Music/Streamrip/Tidal-Max-FLAC"


def test_cover_cache_dir_is_outside_music_output():
    assert cover_cache_dir() == Path.home() / "Library/Application Support/Tidal Max FLAC Studio/cache/covers"


def test_streamrip_config_path_uses_macos_application_support():
    assert streamrip_config_path() == (
        Path.home() / "Library/Application Support/streamrip/config.toml"
    )


def test_streamrip_config_path_uses_windows_appdata(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))

    assert streamrip_config_path("Windows") == tmp_path / "Roaming/streamrip/config.toml"


def test_tool_status_reports_boolean_values(monkeypatch):
    def fake_detect_environment(platform_name=None):
        class Environment:
            tools = {
                "streamrip": type("Tool", (), {"ok": True})(),
                "ffmpeg": type("Tool", (), {"ok": True})(),
                "metaflac": type("Tool", (), {"ok": False})(),
            }

        return Environment()

    monkeypatch.setattr("app.environment.detect_environment", fake_detect_environment)

    assert tool_status() == {"streamrip": True, "ffmpeg": True, "metaflac": False}


def test_setup_status_includes_rich_environment(monkeypatch):
    class Auth:
        bound = False
        user_id = None
        country_code = None
        token_expiry = None

    monkeypatch.setattr("app.config.read_tidal_auth", lambda path: Auth())
    status = setup_status()

    assert "platform" in status
    assert "tools_detail" in status
    assert "package_managers" in status
    assert "manual_commands" in status
    assert set(status["tools"]) == {"streamrip", "ffmpeg", "metaflac"}
