from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_has_direct_release_download_buttons():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Download for macOS" in html
    assert "Download for Windows" in html
    assert "Tidal-Max-FLAC-Studio-macOS.zip" in html
    assert "Tidal-Max-FLAC-Studio-Windows.zip" in html
    assert "releases/download/v0.1.1" in html
