from pathlib import Path

from app.config import default_config, streamrip_config_path, tool_status


def test_default_output_directory_uses_music_streamrip():
    config = default_config()

    assert config.output_dir == Path.home() / "Music/Streamrip/Tidal-Max-FLAC"


def test_streamrip_config_path_uses_macos_application_support():
    assert streamrip_config_path() == (
        Path.home() / "Library/Application Support/streamrip/config.toml"
    )


def test_tool_status_reports_boolean_values(monkeypatch):
    def fake_which(name):
        return "/usr/bin/tool" if name in {"rip", "ffmpeg"} else None

    monkeypatch.setattr("app.config.shutil.which", fake_which)

    assert tool_status() == {"streamrip": True, "ffmpeg": True, "metaflac": False}
