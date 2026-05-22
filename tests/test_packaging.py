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
