from __future__ import annotations

import socket
import threading
import time
import os

import uvicorn

from app.main import app as fastapi_app


HOST = "127.0.0.1"
TITLE = "Tidal Max FLAC Studio"
TOOL_PATHS = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
)


def prime_desktop_environment() -> None:
    current_paths = os.environ.get("PATH", "").split(os.pathsep)
    merged_paths = [path for path in current_paths if path]
    for path in TOOL_PATHS:
        if path not in merged_paths:
            merged_paths.append(path)
    os.environ["PATH"] = os.pathsep.join(merged_paths)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def build_app_url(port: int) -> str:
    return f"http://{HOST}:{port}"


def window_options(url: str) -> dict:
    return {
        "title": TITLE,
        "url": url,
        "width": 1220,
        "height": 780,
        "min_size": (980, 680),
    }


def run_backend(port: int) -> None:
    config = uvicorn.Config(
        fastapi_app,
        host=HOST,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()


def wait_for_backend(port: int, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Local app server did not start in time.")


def main() -> None:
    import webview

    prime_desktop_environment()
    port = find_free_port()
    url = build_app_url(port)
    thread = threading.Thread(target=run_backend, args=(port,), daemon=True)
    thread.start()
    wait_for_backend(port)
    webview.create_window(**window_options(url))
    webview.start()


if __name__ == "__main__":
    main()
