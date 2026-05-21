from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PNG = ASSETS / "app_icon.png"
ICO = ASSETS / "app_icon.ico"
ICNS = ASSETS / "app_icon.icns"
ICONSET = ASSETS / "app_icon.iconset"
SOURCE = ASSETS / "app_icon_source.png"


def content_box(source: Image.Image, threshold: int = 190) -> tuple[int, int, int, int]:
    rgb = source.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            red, green, blue = pixels[x, y]
            luminance = (red * 299 + green * 587 + blue * 114) // 1000
            if luminance < threshold:
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0, 0, width, height)
    return (min(xs), min(ys), max(xs), max(ys))


def crop_square_around_content(source: Image.Image) -> Image.Image:
    left, top, right, bottom = content_box(source)
    content_width = right - left
    content_height = bottom - top
    side = round(max(content_width, content_height) * 1.34)
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    source_width, source_height = source.size
    crop_left = max(0, min(source_width - side, center_x - side // 2))
    crop_top = max(0, min(source_height - side, center_y - side // 2))
    return source.crop((crop_left, crop_top, crop_left + side, crop_top + side))


def source_image_icon(size: int = 1024) -> Image.Image:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source icon image: {SOURCE}")
    crop = crop_square_around_content(Image.open(SOURCE).convert("RGB"))
    resized = crop.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=round(size * 0.21), fill=255)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon.alpha_composite(resized)
    icon.putalpha(mask)
    return icon


def save_iconset(base: Image.Image) -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)
    entries = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    for name, size in entries:
        base.resize((size, size), Image.Resampling.LANCZOS).save(ICONSET / name)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    base = source_image_icon()
    base.save(PNG)

    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(ICO, sizes=ico_sizes)

    save_iconset(base)
    if subprocess.run("command -v iconutil", shell=True, capture_output=True).returncode == 0:
        subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)], check=True)


if __name__ == "__main__":
    main()
