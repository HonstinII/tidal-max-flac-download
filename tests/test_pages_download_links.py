from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_has_direct_release_download_buttons():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Download for macOS" in html
    assert "Download for Windows" in html
    assert "Tidal-Max-FLAC-Studio-macOS.zip" in html
    assert "Tidal-Max-FLAC-Studio-Windows.zip" in html
    assert "releases/download/v0.3.6" in html
    assert html.index("Download for Windows") < html.index("All releases")
    assert html.count("<svg viewBox=") >= 5


def test_pages_has_language_toggle():
    html = (ROOT / "docs" / "index.html").read_text()

    assert 'id="langEn"' in html
    assert 'id="langZh"' in html
    assert "pagesLanguage" in html
    assert "zh-CN" in html
    assert "主要功能" in html


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


def test_pages_has_main_features():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Main features" in html
    assert "macOS and Windows desktop builds" in html
    assert "Tidal authorization through the official Tidal login page" in html
    assert "copyright, ISRC, UPC" in html


def test_pages_omits_interface_preview():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Interface preview" not in html
    assert "ui-shot" not in html
    assert "screen-card" not in html


def test_pages_has_five_usage_steps():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Download and open the app" in html
    assert "Complete the environment check" in html
    assert "Bind Tidal" in html
    assert "Paste a Tidal link" in html
    assert "Choose settings and download" in html
    assert "<br />" in html
