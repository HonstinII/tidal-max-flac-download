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
