from pathlib import Path

from app.lyrics import build_set_lyrics_command, extract_lyrics_text, is_placeholder_lyrics


def test_extract_lyrics_prefers_synced_subtitles():
    assert extract_lyrics_text({"subtitles": "line 1", "lyrics": "plain"}) == "line 1"


def test_extract_lyrics_falls_back_to_plain_lyrics():
    assert extract_lyrics_text({"lyrics": "plain"}) == "plain"


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
