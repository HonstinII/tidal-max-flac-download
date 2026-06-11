from app.updater import check_for_update, is_newer_version, platform_asset_name


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url, timeout=None):
        return FakeResponse(self.payload)


def test_version_compare_handles_v_prefixes():
    assert is_newer_version("v0.3.9", "0.3.8") is True
    assert is_newer_version("v0.3.8", "0.3.8") is False
    assert is_newer_version("v0.3.7", "0.3.8") is False


def test_platform_asset_name_matches_release_assets():
    assert platform_asset_name("Darwin") == "Tidal-Max-FLAC-Studio-macOS.zip"
    assert platform_asset_name("Windows") == "Tidal-Max-FLAC-Studio-Windows.zip"
    assert platform_asset_name("Linux") is None


def test_check_for_update_selects_current_platform_asset():
    session = FakeSession(
        {
            "tag_name": "v0.3.9",
            "html_url": "https://example.test/release",
            "body": "notes",
            "assets": [
                {
                    "name": "Tidal-Max-FLAC-Studio-macOS.zip",
                    "browser_download_url": "https://example.test/mac.zip",
                }
            ],
        }
    )

    info = check_for_update("0.3.8", system="Darwin", session=session)

    assert info.available is True
    assert info.latest_version == "v0.3.9"
    assert info.asset_name == "Tidal-Max-FLAC-Studio-macOS.zip"
    assert info.asset_url == "https://example.test/mac.zip"
