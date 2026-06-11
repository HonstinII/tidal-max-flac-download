from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_has_direct_release_download_buttons():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "Download for macOS" in html
    assert "Download for Windows" in html
    assert "Tidal-Max-FLAC-Studio-macOS.zip" in html
    assert "Tidal-Max-FLAC-Studio-Windows.zip" in html
    assert "releases/download/v0.3.9" in html
    assert html.index("Download for Windows") < html.index("All releases")
    assert html.count("<svg viewBox=") >= 6


def test_pages_has_language_toggle():
    html = (ROOT / "docs" / "index.html").read_text()

    assert 'id="langEn"' in html
    assert 'id="langZh"' in html
    assert "pagesLanguage" in html
    assert "zh-CN" in html
    assert "主要功能" in html


def test_pages_uses_prism_canvas_background():
    html = (ROOT / "docs" / "index.html").read_text()

    assert 'id="prismBackground"' in html
    assert "createPrismBackground" in html
    assert "animationType: \"rotate\"" in html
    assert "baseWidth: 5.5" in html
    assert "timeScale: 0.2" in html
    assert "maxFps: 30" in html
    assert "resolutionScale: 0.58" in html
    assert "document.addEventListener(\"visibilitychange\"" in html
    assert "pointermove" not in html
    assert "hoverStrength" not in html
    assert "assets/prism-background.mp4" not in html
    assert "background-video" not in html


def test_pages_has_button_hover_motion():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "#5fcb97" in html
    assert "a.button::before" in html
    assert "translateY(-101%)" in html
    assert "cubic-bezier(0.2, 0.78, 0.2, 1)" in html
    assert "star-border" in html
    assert "conic-gradient" in html
    assert "star-border-spin 5s linear infinite" in html
    assert "padding: 2px" in html


def test_pages_prism_background_is_visible():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "opacity: 0.94" in html
    assert "brightness(1.45)" in html
    assert "glow: 1.55" in html
    assert "bloom: 1.18" in html


def test_pages_has_telegram_contact_button():
    html = (ROOT / "docs" / "index.html").read_text()

    assert "https://t.me/HonstinHui" in html
    assert "Contact on Telegram" in html
    assert "Telegram 联系我" in html


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
