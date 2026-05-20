from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_builds_macos_and_windows_assets():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert "Tidal-Max-FLAC-Studio-macOS.zip" in workflow
    assert "Tidal-Max-FLAC-Studio-Windows.zip" in workflow
    assert "./scripts/package_macos.sh" in workflow
    assert ".\\scripts\\package_windows.ps1" in workflow
    assert "softprops/action-gh-release@v2" in workflow
