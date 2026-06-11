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


def test_embed_mp4_cover_writes_covr_tag(monkeypatch, tmp_path):
    from app import covers

    class FakeAudio(dict):
        def save(self):
            self["saved"] = ["yes"]

    class FakeCover(bytes):
        FORMAT_JPEG = 13

        def __new__(cls, data, imageformat=None):
            value = bytes.__new__(cls, data)
            value.imageformat = imageformat
            return value

    image = tmp_path / "cover.jpg"
    image.write_bytes(b"jpg")
    audio = FakeAudio()
    monkeypatch.setattr(covers, "download_cover", lambda *args, **kwargs: image)
    monkeypatch.setattr(covers, "MP4", lambda path: audio)
    monkeypatch.setattr(covers, "MP4Cover", FakeCover)

    assert covers.embed_mp4_cover(tmp_path / "song.m4a", "cover-id", tmp_path) is True
    assert audio["covr"][0] == b"jpg"
    assert audio["covr"][0].imageformat == FakeCover.FORMAT_JPEG
    assert audio["saved"] == ["yes"]


def test_save_cover_file_writes_fixed_cover_jpg(monkeypatch, tmp_path):
    from app import covers

    cached = tmp_path / "cached.jpg"
    cached.write_bytes(b"new-cover")
    audio = tmp_path / "Album" / "Song.flac"
    audio.parent.mkdir()
    audio.write_text("audio")
    monkeypatch.setattr(covers, "download_cover", lambda *args, **kwargs: cached)

    result = covers.save_cover_file(audio, "cover-id", tmp_path / "cache")

    assert result == audio.parent / "cover.jpg"
    assert result.read_bytes() == b"new-cover"


def test_save_cover_file_can_skip_or_overwrite_existing(monkeypatch, tmp_path):
    from app import covers

    cached = tmp_path / "cached.jpg"
    cached.write_bytes(b"new-cover")
    audio = tmp_path / "Album" / "Song.flac"
    audio.parent.mkdir()
    audio.write_text("audio")
    existing = audio.parent / "cover.jpg"
    existing.write_bytes(b"old-cover")
    monkeypatch.setattr(covers, "download_cover", lambda *args, **kwargs: cached)

    assert covers.save_cover_file(audio, "cover-id", tmp_path / "cache", "skip") == existing
    assert existing.read_bytes() == b"old-cover"

    assert covers.save_cover_file(audio, "cover-id", tmp_path / "cache", "overwrite") == existing
    assert existing.read_bytes() == b"new-cover"
