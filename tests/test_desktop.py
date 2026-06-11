import app.desktop
from app.desktop import (
    BackendController,
    build_app_url,
    loading_html,
    prime_desktop_environment,
    request_backend_shutdown,
    window_options,
)


def test_build_app_url_uses_loopback_port():
    assert build_app_url(8137) == "http://127.0.0.1:8137"


def test_window_options_targets_local_app_url():
    options = window_options("http://127.0.0.1:8137")

    assert options["title"] == "Tidal Max FLAC Studio"
    assert options["url"] == "http://127.0.0.1:8137"
    assert options["width"] >= 1180
    assert options["height"] >= 760


def test_loading_html_gives_immediate_startup_feedback():
    html = loading_html()

    assert "Tidal Max FLAC Studio" in html
    assert "Starting the local downloader" in html
    assert "meter" in html


def test_desktop_delays_heavy_backend_imports():
    assert not hasattr(app.desktop, "fastapi_app")


def test_prime_desktop_environment_adds_homebrew_paths(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    prime_desktop_environment()

    paths = app.desktop.os.environ["PATH"].split(app.desktop.os.pathsep)
    assert "/opt/homebrew/bin" in paths
    assert "/usr/local/bin" in paths
    assert paths.index("/usr/bin") < paths.index("/opt/homebrew/bin")


def test_request_backend_shutdown_marks_uvicorn_server():
    class Server:
        should_exit = False

    server = Server()
    controller = BackendController(server=server)

    request_backend_shutdown(controller)

    assert server.should_exit is True
