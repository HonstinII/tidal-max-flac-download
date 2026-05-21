from pathlib import Path

from app.folders import open_folder_command, reveal_file_command


def test_open_folder_command_uses_open_on_macos():
    assert open_folder_command(Path("/tmp/music"), "Darwin") == ["open", "/tmp/music"]


def test_open_folder_command_uses_explorer_on_windows():
    assert open_folder_command(Path("C:/Music"), "Windows") == ["explorer", "C:\\Music"]


def test_reveal_file_command_uses_finder_selection_on_macos():
    assert reveal_file_command(Path("/tmp/music/song.flac"), "Darwin") == ["open", "-R", "/tmp/music/song.flac"]


def test_reveal_file_command_uses_explorer_selection_on_windows():
    assert reveal_file_command(Path("C:/Music/song.flac"), "Windows") == ["explorer", "/select,C:\\Music\\song.flac"]
