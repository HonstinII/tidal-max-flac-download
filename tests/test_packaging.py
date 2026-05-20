from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_assets_exist():
    assert (ROOT / "assets" / "app_icon.svg").exists()
    assert (ROOT / "assets" / "app_icon.png").exists()
    assert (ROOT / "assets" / "app_icon.icns").exists()
    assert (ROOT / "assets" / "app_icon.ico").exists()


def test_package_scripts_use_product_name_and_icons():
    macos_script = (ROOT / "scripts" / "package_macos.sh").read_text()
    windows_script = (ROOT / "scripts" / "package_windows.ps1").read_text()

    assert '--name "Tidal Max FLAC Studio"' in macos_script
    assert '--icon "assets/app_icon.icns"' in macos_script
    assert "--osx-bundle-identifier" in macos_script

    assert '--name "Tidal Max FLAC Studio"' in windows_script
    assert '--icon "assets/app_icon.ico"' in windows_script
