from pathlib import Path

from app.environment import candidate_tool_paths
from app.environment import detect_environment
from app.environment import find_tool
from app.environment import managed_tools_dir
from app.environment import prime_runtime_path


def test_macos_detection_finds_homebrew_path(monkeypatch, tmp_path):
    brew = tmp_path / "brew"
    brew.write_text("")
    brew.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    environment = detect_environment("Darwin")

    assert environment.platform.name == "macOS"
    assert environment.package_managers["homebrew"].ok is True
    assert environment.package_managers["homebrew"].path == str(brew)


def test_windows_detection_finds_managed_metaflac(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    metaflac_dir = managed_tools_dir("Windows") / "flac"
    metaflac_dir.mkdir(parents=True)
    metaflac = metaflac_dir / "metaflac.exe"
    metaflac.write_text("")
    metaflac.chmod(0o755)
    monkeypatch.setenv("PATH", "")

    assert find_tool("metaflac", "Windows") == str(metaflac)


def test_runtime_search_path_includes_managed_and_homebrew(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    paths = candidate_tool_paths("Darwin")

    assert "/usr/bin" in paths
    assert "/opt/homebrew/bin" in paths
    assert str(Path.home() / ".local/bin") in paths

    prime_runtime_path("Darwin")
    assert "/opt/homebrew/bin" in candidate_tool_paths("Darwin")
