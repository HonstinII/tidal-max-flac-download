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


def rounded_rectangle_icon(size: int = 1024) -> Image.Image:
    scale = size / 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def box(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
        return tuple(round(v * scale) for v in (x1, y1, x2, y2))

    def width(v: int) -> int:
        return max(1, round(v * scale))

    draw.rounded_rectangle(box(0, 0, 1024, 1024), radius=round(220 * scale), fill="#0E1411")
    draw.rounded_rectangle(
        box(42, 42, 982, 982),
        radius=round(188 * scale),
        outline=(68, 224, 160, 46),
        width=width(18),
    )
    draw.rounded_rectangle(box(170, 212, 854, 812), radius=round(77 * scale), fill="#14211B")
    draw.rectangle(box(262, 300, 762, 416), fill="#F5FAF5")
    draw.rectangle(box(452, 300, 572, 724), fill="#F5FAF5")

    wave = [
        (256, 616),
        (312, 616),
        (312, 548),
        (368, 548),
        (423, 548),
        (423, 684),
        (479, 684),
        (535, 684),
        (535, 548),
        (591, 548),
        (646, 548),
        (646, 616),
        (702, 616),
        (758, 616),
        (758, 548),
        (814, 548),
    ]
    wave = [(round(x * scale), round(y * scale)) for x, y in wave]
    draw.line(wave, fill="#44E0A0", width=width(38), joint="curve")
    for point in wave:
        draw.ellipse(
            (
                point[0] - width(19),
                point[1] - width(19),
                point[0] + width(19),
                point[1] + width(19),
            ),
            fill="#44E0A0",
        )
    draw.line([box(276, 724, 360, 724)[:2], box(276, 724, 360, 724)[2:]], fill="#44E0A0", width=width(38))
    draw.line([box(664, 724, 748, 724)[:2], box(664, 724, 748, 724)[2:]], fill="#44E0A0", width=width(38))
    return img


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
    base = rounded_rectangle_icon()
    base.save(PNG)

    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(ICO, sizes=ico_sizes)

    save_iconset(base)
    if subprocess.run("command -v iconutil", shell=True, capture_output=True).returncode == 0:
        subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)], check=True)


if __name__ == "__main__":
    main()
