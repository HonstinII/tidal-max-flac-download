from pathlib import Path

from app.lyrics import build_set_lyrics_command, extract_lyrics_text, is_placeholder_lyrics, write_lrc


def test_extract_lyrics_prefers_synced_subtitles():
    assert extract_lyrics_text({"subtitles": "line 1", "lyrics": "plain"}) == "line 1"


def test_extract_lyrics_falls_back_to_plain_lyrics():
    assert extract_lyrics_text({"lyrics": "plain"}) == "plain"


def test_extract_lyrics_can_force_plain_mode():
    payload = {"subtitles": "[00:01.00] synced", "lyrics": "plain"}

    assert extract_lyrics_text(payload, mode="plain") == "plain"


def test_extract_lyrics_can_force_synced_mode():
    payload = {"subtitles": "[00:01.00] synced", "lyrics": "plain"}

    assert extract_lyrics_text(payload, mode="synced") == "[00:01.00] synced"


def test_extract_lyrics_synced_mode_does_not_fallback_to_plain():
    assert extract_lyrics_text({"lyrics": "plain"}, mode="synced") == ""


def test_extract_lyrics_rejects_hash_placeholder_text():
    assert extract_lyrics_text({"subtitles": "[00:01.00] ####################"}) == ""


def test_placeholder_detector_ignores_real_timestamps():
    assert is_placeholder_lyrics("[00:01.00] real words here") is False
    assert is_placeholder_lyrics("[00:01.00] ####################") is True


def test_build_set_lyrics_command_writes_vorbis_comment():
    command = build_set_lyrics_command(Path("/tmp/song.flac"), "hello")

    assert command == [
        "metaflac",
        "--set-tag=LYRICS=hello",
        "/tmp/song.flac",
    ]


def test_write_lrc_creates_same_stem_sidecar(tmp_path):
    flac = tmp_path / "song.flac"

    lrc = write_lrc(flac, "[00:01.00] line")

    assert lrc == tmp_path / "song.lrc"
    assert lrc.read_text(encoding="utf-8") == "[00:01.00] line\n"


def test_embed_mp4_lyrics_writes_mp4_lyrics_tag(monkeypatch, tmp_path):
    from app import lyrics

    class FakeAudio(dict):
        def save(self):
            self["saved"] = ["yes"]

    audio = FakeAudio()
    monkeypatch.setattr(lyrics, "MP4", lambda path: audio)

    assert lyrics.embed_mp4_lyrics(tmp_path / "song.m4a", "hello") is True
    assert audio["\xa9lyr"] == ["hello"]
    assert audio["saved"] == ["yes"]
