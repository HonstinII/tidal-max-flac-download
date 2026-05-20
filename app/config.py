from dataclasses import dataclass
from pathlib import Path
import shutil

from .tidal_config import read_tidal_auth


@dataclass(frozen=True)
class AppConfig:
    streamrip_config: Path
    output_dir: Path
    concurrency: int = 10
    embed_covers: bool = True
    skip_existing: bool = True


def streamrip_config_path() -> Path:
    return Path.home() / "Library/Application Support/streamrip/config.toml"


def default_config() -> AppConfig:
    return AppConfig(
        streamrip_config=streamrip_config_path(),
        output_dir=Path.home() / "Music/Streamrip/Tidal-Max-FLAC",
    )


def tool_status() -> dict[str, bool]:
    streamrip_venv = Path.home() / "Applications/streamrip-dev/bin/rip"
    return {
        "streamrip": shutil.which("rip") is not None
        or shutil.which("streamrip") is not None
        or streamrip_venv.exists(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "metaflac": shutil.which("metaflac") is not None,
    }


def setup_status() -> dict:
    config = default_config()
    tidal_auth = read_tidal_auth(config.streamrip_config)
    return {
        "tools": tool_status(),
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
