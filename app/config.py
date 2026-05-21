from dataclasses import dataclass
import os
import platform
from pathlib import Path

from .environment import detect_environment
from .environment import tool_status as environment_tool_status
from .tidal_config import read_tidal_auth


@dataclass(frozen=True)
class AppConfig:
    streamrip_config: Path
    output_dir: Path
    concurrency: int = 10
    embed_covers: bool = True
    skip_existing: bool = True


def streamrip_config_path(platform_name: str | None = None) -> Path:
    platform_name = platform_name or platform.system()
    if platform_name == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "streamrip/config.toml"
    return Path.home() / "Library/Application Support/streamrip/config.toml"


def default_config() -> AppConfig:
    return AppConfig(
        streamrip_config=streamrip_config_path(),
        output_dir=Path.home() / "Music/Streamrip/Tidal-Max-FLAC",
    )


def tool_status() -> dict[str, bool]:
    return environment_tool_status()


def setup_status() -> dict:
    config = default_config()
    tidal_auth = read_tidal_auth(config.streamrip_config)
    environment = detect_environment().to_dict()
    return {
        "tools": tool_status(),
        "platform": environment["platform"],
        "tools_detail": environment["tools"],
        "package_managers": environment["package_managers"],
        "manual_commands": environment["manual_commands"],
        "manual_urls": environment["manual_urls"],
        "search_paths": environment["search_paths"],
        "streamrip_config": {
            "path": str(config.streamrip_config),
            "exists": config.streamrip_config.exists(),
        },
        "output_dir": str(config.output_dir),
        "tidal": {
            "bound": tidal_auth.bound,
            "user_id": tidal_auth.user_id,
            "country_code": tidal_auth.country_code,
            "token_expiry": tidal_auth.token_expiry,
        },
    }
