from pathlib import Path

from app.lyrics import build_set_lyrics_command, extract_lyrics_text


def test_extract_lyrics_prefers_synced_subtitles():
    assert extract_lyrics_text({"subtitles": "line 1", "lyrics": "plain"}) == "line 1"


def test_extract_lyrics_falls_back_to_plain_lyrics():
    assert extract_lyrics_text({"lyrics": "plain"}) == "plain"


def test_build_set_lyrics_command_writes_vorbis_comment():
    command = build_set_lyrics_command(Path("/tmp/song.flac"), "hello")

    assert command == [
        "metaflac",
        "--remove-tag=LYRICS",
        "--set-tag=LYRICS=hello",
        "/tmp/song.flac",
    ]
