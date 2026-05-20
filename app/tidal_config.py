from dataclasses import dataclass
from pathlib import Path

import tomlkit


@dataclass(frozen=True)
class TidalAuthState:
    bound: bool
    user_id: str | None = None
    country_code: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: float | None = None


@dataclass(frozen=True)
class TidalToken:
    user_id: str
    country_code: str
    access_token: str
    refresh_token: str
    token_expiry: float


def read_tidal_auth(path: Path) -> TidalAuthState:
    if not path.exists():
        return TidalAuthState(bound=False)

    doc = tomlkit.parse(path.read_text(encoding="utf-8"))
    tidal = doc.get("tidal")
    if not isinstance(tidal, dict):
        return TidalAuthState(bound=False)

    access_token = str(tidal.get("access_token") or "")
    refresh_token = str(tidal.get("refresh_token") or "")
    if not access_token or not refresh_token:
        return TidalAuthState(bound=False)

    token_expiry = tidal.get("token_expiry")
    return TidalAuthState(
        bound=True,
        user_id=str(tidal.get("user_id") or ""),
        country_code=str(tidal.get("country_code") or ""),
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=float(token_expiry) if token_expiry not in (None, "") else None,
    )


def write_tidal_auth(path: Path, token: TidalToken) -> None:
    if path.exists():
        doc = tomlkit.parse(path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()

    if "tidal" not in doc or not isinstance(doc["tidal"], dict):
        doc["tidal"] = tomlkit.table()

    tidal = doc["tidal"]
    tidal["user_id"] = token.user_id
    tidal["country_code"] = token.country_code
    tidal["access_token"] = token.access_token
    tidal["refresh_token"] = token.refresh_token
    tidal["token_expiry"] = token.token_expiry

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def clear_tidal_auth(path: Path) -> None:
    if path.exists():
        doc = tomlkit.parse(path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()

    if "tidal" not in doc or not isinstance(doc["tidal"], dict):
        doc["tidal"] = tomlkit.table()

    tidal = doc["tidal"]
    tidal["user_id"] = ""
    tidal["country_code"] = ""
    tidal["access_token"] = ""
    tidal["refresh_token"] = ""
    tidal["token_expiry"] = ""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
