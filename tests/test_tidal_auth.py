import time

from requests.exceptions import JSONDecodeError

from app.tidal_auth import TidalAuthManager


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.posts = []

    def post(self, url, data=None, auth=None, timeout=None):
        self.posts.append({"url": url, "data": data, "auth": auth, "timeout": timeout})
        return FakeResponse(self.payloads.pop(0))


def test_start_returns_session_id_and_tidal_url():
    session = FakeSession(
        [{"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"}]
    )
    manager = TidalAuthManager(session=session)

    auth_session = manager.start()

    assert auth_session.session_id
    assert auth_session.url == "https://link.tidal.com/ABCDE"
    assert auth_session.expires_in == 600


def test_poll_pending_returns_pending_status():
    session = FakeSession(
        [
            {"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"},
            {"status": 400, "sub_status": 1002},
        ]
    )
    manager = TidalAuthManager(session=session)
    auth_session = manager.start()

    result = manager.poll(auth_session.session_id)

    assert result.status == "pending"
    assert result.token is None


def test_poll_oauth_pending_returns_pending_status():
    session = FakeSession(
        [
            {"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"},
            {"error": "authorization_pending"},
        ]
    )
    manager = TidalAuthManager(session=session)
    auth_session = manager.start()

    result = manager.poll(auth_session.session_id)

    assert result.status == "pending"
    assert result.token is None


def test_poll_non_json_response_returns_error_status():
    session = FakeSession(
        [
            {"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"},
            JSONDecodeError("Expecting value", "", 0),
        ]
    )
    manager = TidalAuthManager(session=session)
    auth_session = manager.start()

    result = manager.poll(auth_session.session_id)

    assert result.status == "error"
    assert "non-JSON" in result.message


def test_poll_success_maps_tidal_token():
    session = FakeSession(
        [
            {"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"},
            {
                "user": {"userId": "123", "countryCode": "US"},
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
            },
        ]
    )
    manager = TidalAuthManager(session=session, clock=lambda: 1000)
    auth_session = manager.start()

    result = manager.poll(auth_session.session_id)

    assert result.status == "success"
    assert result.token.user_id == "123"
    assert result.token.country_code == "US"
    assert result.token.access_token == "access"
    assert result.token.refresh_token == "refresh"
    assert result.token.token_expiry == 4600


def test_poll_expired_session_returns_expired():
    session = FakeSession(
        [{"deviceCode": "device-1", "verificationUriComplete": "link.tidal.com/ABCDE"}]
    )
    manager = TidalAuthManager(session=session, clock=lambda: time.time() + 1000)
    auth_session = manager.start()
    manager.sessions[auth_session.session_id].created_at = 0

    result = manager.poll(auth_session.session_id)

    assert result.status == "expired"
