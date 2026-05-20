from pathlib import Path

from app.folders import open_folder_command


def test_open_folder_command_uses_open_on_macos():
    assert open_folder_command(Path("/tmp/music"), "Darwin") == ["open", "/tmp/music"]


def test_open_folder_command_uses_explorer_on_windows():
    assert open_folder_command(Path("C:/Music"), "Windows") == ["explorer", "C:\\Music"]
