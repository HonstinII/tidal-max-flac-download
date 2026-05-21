from app.tidal_api import TrackItem


def track():
    return TrackItem(
        track_id="1",
        title="Song",
        artist="Artist",
        album_title="Album",
        album_artist="Album Artist",
        album_year="2026",
        cover_id="cover",
        track_number=7,
    )


def test_repair_flac_tags_rewrites_core_metadata(monkeypatch, tmp_path):
    from app import metadata

    class FakeAudio(dict):
        pictures = []

        def save(self):
            self["saved"] = ["yes"]

    audio = FakeAudio()
    monkeypatch.setattr(metadata, "FLAC", lambda path: audio)

    assert metadata.repair_flac_tags(tmp_path / "song.flac", track()) is True
    assert audio["title"] == ["Song"]
    assert audio["artist"] == ["Artist"]
    assert audio["album"] == ["Album"]
    assert audio["albumartist"] == ["Album Artist"]
    assert audio["date"] == ["2026"]
    assert audio["tracknumber"] == ["7"]
    assert audio["saved"] == ["yes"]


def test_has_cover_reads_flac_picture_blocks(monkeypatch, tmp_path):
    from app import metadata

    class WithCover:
        pictures = [object()]

    class WithoutCover:
        pictures = []

    monkeypatch.setattr(metadata, "FLAC", lambda path: WithCover())
    assert metadata.has_cover(tmp_path / "with.flac") is True

    monkeypatch.setattr(metadata, "FLAC", lambda path: WithoutCover())
    assert metadata.has_cover(tmp_path / "without.flac") is False
