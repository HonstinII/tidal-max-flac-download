from pathlib import Path

from app.folders import existing_folder_or_parent, open_folder_command, reveal_file_command


def test_open_folder_command_uses_open_on_macos():
    assert open_folder_command(Path("/tmp/music"), "Darwin") == ["open", "/tmp/music"]


def test_open_folder_command_uses_explorer_on_windows():
    assert open_folder_command(Path("C:/Music"), "Windows") == ["explorer", "C:\\Music"]


def test_reveal_file_command_uses_finder_selection_on_macos():
    assert reveal_file_command(Path("/tmp/music/song.flac"), "Darwin") == ["open", "-R", "/tmp/music/song.flac"]


def test_reveal_file_command_uses_explorer_selection_on_windows():
    assert reveal_file_command(Path("C:/Music/song.flac"), "Windows") == ["explorer", "/select,C:\\Music\\song.flac"]


def test_existing_folder_or_parent_uses_nearest_existing_parent(tmp_path):
    parent = tmp_path / "music"
    parent.mkdir()

    assert existing_folder_or_parent(parent / "deleted" / "album") == parent


def test_existing_folder_or_parent_uses_parent_for_file(tmp_path):
    file_path = tmp_path / "song.flac"
    file_path.write_text("audio")

    assert existing_folder_or_parent(file_path) == tmp_path
