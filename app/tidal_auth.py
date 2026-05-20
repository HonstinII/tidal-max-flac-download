import base64
import time
import uuid
from dataclasses import dataclass
from typing import Callable

import requests
from requests.auth import HTTPBasicAuth

from .tidal_config import TidalToken

AUTH_URL = "https://auth.tidal.com/v1/oauth2"
CLIENT_ID = base64.b64decode("elU0WEhWVmtjMnREUG80dA==").decode("iso-8859-1")
CLIENT_SECRET = base64.b64decode(
    "VkpLaERGcUpQcXZzUFZOQlY2dWtYVEptd2x2YnR0UDd3bE1scmM3MnNlND0="
).decode("iso-8859-1")
AUTH = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)


@dataclass
class AuthSession:
    session_id: str
    device_code: str
    url: str
    created_at: float
    expires_in: int = 600


@dataclass(frozen=True)
class AuthPollResult:
    status: str
    token: TidalToken | None = None
    message: str | None = None


class TidalAuthManager:
    def __init__(
        self,
        session=None,
        clock: Callable[[], float] | None = None,
        timeout_s: int = 600,
    ):
        self.session = session or requests.Session()
        self.clock = clock or time.time
        self.timeout_s = timeout_s
        self.sessions: dict[str, AuthSession] = {}

    def start(self) -> AuthSession:
        response = self.session.post(
            f"{AUTH_URL}/device_authorization",
            data={"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        session = AuthSession(
            session_id=str(uuid.uuid4()),
            device_code=payload["deviceCode"],
            url=_normalize_tidal_url(payload["verificationUriComplete"]),
            created_at=self.clock(),
            expires_in=self.timeout_s,
        )
        self.sessions[session.session_id] = session
        return session

    def poll(self, session_id: str) -> AuthPollResult:
        session = self.sessions.get(session_id)
        if session is None:
            return AuthPollResult(status="missing", message="Unknown auth session.")
        if self.clock() - session.created_at > session.expires_in:
            return AuthPollResult(status="expired", message="Authorization expired.")

        response = self.session.post(
            f"{AUTH_URL}/token",
            data={
                "client_id": CLIENT_ID,
                "device_code": session.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "scope": "r_usr+w_usr+w_sub",
            },
            auth=AUTH,
            timeout=30,
        )
        payload = response.json()
        if "status" in payload and payload["status"] != 200:
            if payload["status"] == 400 and payload.get("sub_status") == 1002:
                return AuthPollResult(status="pending")
            return AuthPollResult(status="error", message=str(payload))

        return AuthPollResult(
            status="success",
            token=TidalToken(
                user_id=str(payload["user"]["userId"]),
                country_code=str(payload["user"]["countryCode"]),
                access_token=str(payload["access_token"]),
                refresh_token=str(payload["refresh_token"]),
                token_expiry=float(payload["expires_in"]) + self.clock(),
            ),
        )


def _normalize_tidal_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"
