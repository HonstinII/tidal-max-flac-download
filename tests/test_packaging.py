from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_assets_exist():
    assert (ROOT / "assets" / "app_icon_source.png").exists()
    assert (ROOT / "assets" / "app_icon.png").exists()
    assert (ROOT / "assets" / "app_icon.icns").exists()
    assert (ROOT / "assets" / "app_icon.ico").exists()


def test_package_scripts_use_product_name_and_icons():
    macos_script = (ROOT / "scripts" / "package_macos.sh").read_text()
    windows_script = (ROOT / "scripts" / "package_windows.ps1").read_text()

    assert '--name "Tidal Max FLAC Studio"' in macos_script
    assert '--icon "assets/app_icon.icns"' in macos_script
    assert "--osx-bundle-identifier" in macos_script
    assert '--add-data "app/tools:app/tools"' in macos_script

    assert '--name "Tidal Max FLAC Studio"' in windows_script
    assert '--icon "assets/app_icon.ico"' in windows_script
    assert '--add-data "app/tools;app/tools"' in windows_script


def test_cover_tool_modal_has_manual_recovery_actions():
    html = (ROOT / "app" / "static" / "index.html").read_text()
    js = (ROOT / "app" / "static" / "app.js").read_text()

    assert "manualCoverToolLink" in html
    assert "https://xiph.org/flac/download.html" in html
    assert "recheckCoverToolButton" in html
    assert "coverToolManualCopy" in js


def test_settings_modal_groups_advanced_controls():
    html = (ROOT / "app" / "static" / "index.html").read_text()
    css = (ROOT / "app" / "static" / "styles.css").read_text()
    js = (ROOT / "app" / "static" / "app.js").read_text()

    assert "settings-row wide-control" in html
    assert "settings-select-row" in html
    assert "settings-select-control" in html
    assert "native-hidden-select" in html
    assert "compact-dropdown" in html
    assert "data-select-target=\"lyricsMode\"" in html
    assert "data-select-target=\"existingStrategy\"" in html
    assert "data-select-target=\"coverFileStrategy\"" in html
    assert 'id="saveCoverFile"' in html
    assert 'id="coverFileStrategy"' in html
    assert html.index('id="concurrency"') < html.index('id="writeLrc"')
    assert html.index('id="writeLrc"') < html.index('id="saveCoverFile"')
    assert html.index('id="lyricsMode"') < html.index('id="existingStrategy"')
    assert html.index('id="existingStrategy"') < html.index('id="coverFileStrategy"')
    assert "data-tooltip-key=\"concurrencyHelp\"" in html
    assert ".info-dot::after" in css
    assert ".compact-select-menu" in css
    assert "align-items: start" in css
    assert "data-tooltip" in css
    assert "dataset.tooltip" in js
    assert "syncCustomSelects" in js
    assert "save_cover_file" in js
    assert "cover_file_strategy" in js
    assert "include_transient=true" in js


def test_update_modal_supports_confirm_before_download():
    html = (ROOT / "app" / "static" / "index.html").read_text()
    js = (ROOT / "app" / "static" / "app.js").read_text()

    assert 'id="updateModal"' in html
    assert 'id="downloadUpdateButton"' in html
    assert 'id="openReleaseButton"' in html
    assert 'id="laterUpdateButton"' in html
    assert "/api/update/check" in js
    assert "/api/update/download" in js
    assert "dismissedUpdateTag" in js
    assert "checkForUpdates" in js
