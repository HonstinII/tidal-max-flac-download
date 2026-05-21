import platform
import subprocess
from pathlib import Path


def open_folder_command(path: Path, system: str | None = None) -> list[str]:
    system = system or platform.system()
    if system == "Darwin":
        return ["open", str(path)]
    if system == "Windows":
        return ["explorer", str(path).replace("/", "\\")]
    return ["xdg-open", str(path)]


def reveal_file_command(path: Path, system: str | None = None) -> list[str]:
    system = system or platform.system()
    if system == "Darwin":
        return ["open", "-R", str(path)]
    if system == "Windows":
        windows_path = str(path).replace("/", "\\")
        return ["explorer", f"/select,{windows_path}"]
    return ["xdg-open", str(path.parent)]


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(open_folder_command(path))


def reveal_file(path: Path) -> None:
    subprocess.Popen(reveal_file_command(path))


def pick_folder(initial: Path) -> Path | None:
    system = platform.system()
    if system == "Darwin":
        script = (
            'POSIX path of (choose folder with prompt "Choose output folder" '
            f'default location POSIX file "{initial}")'
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        return Path(result.stdout.strip())

    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    selected = filedialog.askdirectory(initialdir=str(initial))
    root.destroy()
    return Path(selected) if selected else None
