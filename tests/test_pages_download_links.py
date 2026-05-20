from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_has_direct_release_download_buttons():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Download for macOS" in html
    assert "Download for Windows" in html
    assert "Tidal-Max-FLAC-Studio-macOS.zip" in html
    assert "Tidal-Max-FLAC-Studio-Windows.zip" in html
    assert "releases/download/v0.1.1" in html


def test_pages_omits_explainer_cards():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "You do not enter the product from GitHub Pages" not in html
    assert "Download the desktop app" not in html


def test_pages_credits_project_author_and_streamrip():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Tidal Max FLAC Studio by" in html
    assert "HonstinII" in html
    assert "streamrip" in html
    assert "nathom" in html


def test_pages_has_three_usage_steps():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Prepare the environment" in html
    assert "Link Tidal" in html
    assert "Paste URLs and download" in html
    assert "If streamrip, ffmpeg, or metaflac is missing" in html
    assert "<br />" in html
