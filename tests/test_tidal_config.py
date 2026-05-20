from pathlib import Path

from app.tidal_config import TidalToken, read_tidal_auth, write_tidal_auth


def test_missing_config_returns_unbound_state(tmp_path):
    state = read_tidal_auth(tmp_path / "missing.toml")

    assert state.bound is False
    assert state.country_code is None


def test_empty_token_fields_return_unbound_state(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('[tidal]\naccess_token = ""\nrefresh_token = ""\n', encoding="utf-8")

    state = read_tidal_auth(config)

    assert state.bound is False


def test_existing_token_fields_return_bound_state(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        "\n".join(
            [
                "[tidal]",
                'user_id = "123"',
                'country_code = "US"',
                'access_token = "access"',
                'refresh_token = "refresh"',
                "token_expiry = 1779276890.5",
            ]
        ),
        encoding="utf-8",
    )

    state = read_tidal_auth(config)

    assert state.bound is True
    assert state.user_id == "123"
    assert state.country_code == "US"
    assert state.token_expiry == 1779276890.5


def test_write_tidal_auth_preserves_unrelated_config(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        "\n".join(
            [
                "[downloads]",
                'folder = "/tmp/music"',
                "",
                "[tidal]",
                'quality = 3',
                'access_token = ""',
            ]
        ),
        encoding="utf-8",
    )

    write_tidal_auth(
        config,
        TidalToken(
            user_id="42",
            country_code="GB",
            access_token="new-access",
            refresh_token="new-refresh",
            token_expiry=1234.5,
        ),
    )

    text = config.read_text(encoding="utf-8")
    assert 'folder = "/tmp/music"' in text
    assert "quality = 3" in text
    assert 'user_id = "42"' in text
    assert 'country_code = "GB"' in text
    assert 'access_token = "new-access"' in text
    assert 'refresh_token = "new-refresh"' in text
    assert "token_expiry = 1234.5" in text
