from __future__ import annotations

from dataclasses import dataclass
import socket
import threading
import time
import os

from app.environment import prime_runtime_path


HOST = "127.0.0.1"
TITLE = "Tidal Max FLAC Studio"


@dataclass
class BackendController:
    server: object | None = None
    error: Exception | None = None


def prime_desktop_environment() -> None:
    prime_runtime_path()


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def build_app_url(port: int) -> str:
    return f"http://{HOST}:{port}"


def loading_html() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        color-scheme: dark;
        --bg: #0d1310;
        --panel: #15201a;
        --line: #304139;
        --text: #f2f7f1;
        --muted: #b7c5bb;
        --accent: #46d8a1;
        --amber: #f3be3f;
      }
      * { box-sizing: border-box; }
      html, body {
        width: 100%;
        height: 100%;
        margin: 0;
        background:
          radial-gradient(circle at 74% 16%, rgba(243, 190, 63, 0.14), transparent 34%),
          linear-gradient(135deg, #0d1813, var(--bg) 58%, #0a0d0b);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      body {
        display: grid;
        place-items: center;
      }
      main {
        width: min(520px, calc(100vw - 48px));
        border: 1px solid var(--line);
        background: rgba(21, 32, 26, 0.78);
        padding: 28px;
        box-shadow: 0 28px 90px rgba(0, 0, 0, 0.38);
      }
      p {
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }
      .kicker {
        margin-bottom: 10px;
        color: var(--amber);
        font-size: 12px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0 0 12px;
        font-size: clamp(34px, 7vw, 56px);
        line-height: 0.94;
        letter-spacing: 0;
      }
      .meter {
        overflow: hidden;
        height: 8px;
        margin-top: 24px;
        border: 1px solid var(--line);
        background: #0b100d;
      }
      .meter i {
        display: block;
        width: 42%;
        height: 100%;
        background: var(--accent);
        animation: load 1s ease-in-out infinite alternate;
      }
      @keyframes load {
        from { transform: translateX(-50%); }
        to { transform: translateX(160%); }
      }
    </style>
  </head>
  <body>
    <main>
      <p class="kicker">Local audio workstation</p>
      <h1>Tidal Max FLAC Studio</h1>
      <p>Starting the local downloader...</p>
      <div class="meter" aria-hidden="true"><i></i></div>
    </main>
  </body>
</html>
"""


def window_options(url: str) -> dict:
    return {
        "title": TITLE,
        "url": url,
        "width": 1220,
        "height": 780,
        "min_size": (980, 680),
    }


def run_backend(port: int, controller: BackendController | None = None) -> None:
    import uvicorn

    from app.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host=HOST,
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    if controller is not None:
        controller.server = server
    try:
        server.run()
    except Exception as error:  # pragma: no cover - defensive desktop startup path
        if controller is not None:
            controller.error = error
        raise


def request_backend_shutdown(controller: BackendController) -> None:
    server = controller.server
    if server is not None:
        setattr(server, "should_exit", True)


def wait_for_backend(port: int, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Local app server did not start in time.")


def start_backend_and_load(window, port: int, url: str, controller: BackendController) -> None:
    prime_desktop_environment()
    thread = threading.Thread(target=run_backend, args=(port, controller), daemon=True)
    thread.start()
    try:
        wait_for_backend(port)
    except Exception as error:
        controller.error = error
        window.load_html(
            loading_html().replace(
                "Starting the local downloader...",
                f"Startup failed: {error}",
            )
        )
        return
    window.load_url(url)


def install_close_handler(window, controller: BackendController) -> None:
    def on_closing():
        try:
            window.hide()
        finally:
            request_backend_shutdown(controller)

    window.events.closing += on_closing


def main() -> None:
    import webview

    port = find_free_port()
    url = build_app_url(port)
    controller = BackendController()
    window = webview.create_window(
        **{**window_options(url), "url": None, "html": loading_html()}
    )
    install_close_handler(window, controller)
    webview.start(start_backend_and_load, (window, port, url, controller))


if __name__ == "__main__":
    main()
