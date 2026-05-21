import app.desktop
from app.desktop import build_app_url, window_options


def test_build_app_url_uses_loopback_port():
    assert build_app_url(8137) == "http://127.0.0.1:8137"


def test_window_options_targets_local_app_url():
    options = window_options("http://127.0.0.1:8137")

    assert options["title"] == "Tidal Max FLAC Studio"
    assert options["url"] == "http://127.0.0.1:8137"
    assert options["width"] >= 1180
    assert options["height"] >= 760


def test_desktop_imports_fastapi_app_for_packaging():
    assert app.desktop.fastapi_app.title == "Tidal Max FLAC Studio"
