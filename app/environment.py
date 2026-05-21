from __future__ import annotations

import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


TOOL_NAMES = ("streamrip", "ffmpeg", "metaflac")
MACOS_TOOL_PATHS = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
)


@dataclass(frozen=True)
class PlatformInfo:
    system: str
    name: str
    supports_auto_install: bool


@dataclass(frozen=True)
class ToolInfo:
    ok: bool
    required: bool
    path: str | None
    installable: bool
    description: str


@dataclass(frozen=True)
class PackageManagerInfo:
    ok: bool
    path: str | None


@dataclass(frozen=True)
class EnvironmentInfo:
    platform: PlatformInfo
    tools: dict[str, ToolInfo]
    package_managers: dict[str, PackageManagerInfo]
    manual_commands: dict[str, str]
    search_paths: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def app_data_dir(platform_name: str | None = None) -> Path:
    platform_name = platform_name or platform.system()
    if platform_name == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Tidal Max FLAC Studio"
    if platform_name == "Darwin":
        return Path.home() / "Library/Application Support/Tidal Max FLAC Studio"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "tidal-max-flac-studio"


def managed_tools_dir(platform_name: str | None = None) -> Path:
    return app_data_dir(platform_name) / "tools"


def candidate_tool_paths(platform_name: str | None = None) -> list[str]:
    platform_name = platform_name or platform.system()
    paths = [path for path in os.environ.get("PATH", "").split(os.pathsep) if path]
    managed = managed_tools_dir(platform_name)
    extras = [
        str(managed),
        str(managed / "flac"),
        str(managed / "ffmpeg" / "bin"),
        str(Path.home() / ".local/bin"),
    ]
    if platform_name == "Windows":
        extras.extend(
            [
                str(managed / "flac" / "bin"),
                str(Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "Python/Scripts"),
            ]
        )
    if platform_name == "Darwin":
        extras.extend(MACOS_TOOL_PATHS)

    merged: list[str] = []
    for path in [*paths, *extras]:
        if path and path not in merged:
            merged.append(path)
    return merged


def find_tool(name: str, platform_name: str | None = None) -> str | None:
    search_path = os.pathsep.join(candidate_tool_paths(platform_name))
    names = [name]
    if name == "streamrip":
        names = ["rip", "streamrip"]
    if platform_name == "Windows":
        names = [item if item.endswith(".exe") else f"{item}.exe" for item in names] + names
    for candidate in names:
        found = shutil.which(candidate, path=search_path)
        if found:
            return found
    if name == "streamrip":
        streamrip_venv = Path.home() / "Applications/streamrip-dev/bin/rip"
        if streamrip_venv.exists():
            return str(streamrip_venv)
    return None


def detect_platform(platform_name: str | None = None) -> PlatformInfo:
    system = platform_name or platform.system()
    name = {"Darwin": "macOS", "Windows": "Windows"}.get(system, system or "Unknown")
    return PlatformInfo(system=system, name=name, supports_auto_install=system in {"Darwin", "Windows"})


def detect_environment(platform_name: str | None = None) -> EnvironmentInfo:
    platform_info = detect_platform(platform_name)
    system = platform_info.system
    package_managers = {
        "homebrew": PackageManagerInfo(
            ok=(brew := find_tool("brew", system)) is not None,
            path=brew,
        ),
        "winget": PackageManagerInfo(
            ok=(winget := find_tool("winget", system)) is not None,
            path=winget,
        ),
    }
    tools = {
        "streamrip": ToolInfo(
            ok=(streamrip := find_tool("streamrip", system)) is not None,
            required=True,
            path=streamrip,
            installable=True,
            description="Core download tool that manages Tidal-compatible download configuration.",
        ),
        "ffmpeg": ToolInfo(
            ok=(ffmpeg := find_tool("ffmpeg", system)) is not None,
            required=True,
            path=ffmpeg,
            installable=system in {"Darwin", "Windows"},
            description="Core audio processor used to assemble and write FLAC files.",
        ),
        "metaflac": ToolInfo(
            ok=(metaflac := find_tool("metaflac", system)) is not None,
            required=False,
            path=metaflac,
            installable=system in {"Darwin", "Windows"},
            description="Optional metadata helper for embedding cover art into FLAC files.",
        ),
    }
    return EnvironmentInfo(
        platform=platform_info,
        tools=tools,
        package_managers=package_managers,
        manual_commands=manual_commands(system),
        search_paths=candidate_tool_paths(system),
    )


def manual_commands(platform_name: str) -> dict[str, str]:
    if platform_name == "Windows":
        return {
            "streamrip": "python -m pip install --user streamrip",
            "ffmpeg": "winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements",
            "metaflac": "Use bundled FLAC tools or install FLAC manually, then recheck.",
        }
    return {
        "homebrew": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
        "streamrip": "python3 -m pip install --user streamrip",
        "ffmpeg": "brew install ffmpeg",
        "metaflac": "brew install flac",
    }


def tool_status(platform_name: str | None = None) -> dict[str, bool]:
    environment = detect_environment(platform_name)
    return {name: info.ok for name, info in environment.tools.items()}


def prime_runtime_path(platform_name: str | None = None) -> None:
    os.environ["PATH"] = os.pathsep.join(candidate_tool_paths(platform_name))
