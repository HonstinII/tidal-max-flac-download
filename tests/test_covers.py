from pathlib import Path

from app.covers import build_cover_url, build_metaflac_command


def test_build_cover_url_uses_tidal_image_path():
    assert build_cover_url("a-b-c", 1280) == (
        "https://resources.tidal.com/images/a/b/c/1280x1280.jpg"
    )


def test_build_metaflac_command_imports_front_cover():
    command = build_metaflac_command(Path("/tmp/song.flac"), Path("/tmp/cover.jpg"))

    assert command == [
        "metaflac",
        "--import-picture-from=3|image/jpeg|||/tmp/cover.jpg",
        "/tmp/song.flac",
    ]
