#!/usr/bin/env python3
"""Export application icons from frontend/public/icon.svg (ImageMagick + Pillow)."""

from io import BytesIO
from pathlib import Path
import shutil
import subprocess

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public"


def main():
    magick = shutil.which("magick")
    if magick is None:
        raise SystemExit("ImageMagick 7 is required: install it before exporting icons.")

    result = subprocess.run(
        [magick, "-background", "none", str(PUBLIC / "icon.svg"),
         "-resize", "1024x1024", "png:-"],
        check=True, capture_output=True,
    )
    with Image.open(BytesIO(result.stdout)) as rendered:
        master = rendered.convert("RGBA")

    for size in (180, 192, 256, 512):
        master.resize((size, size), Image.Resampling.LANCZOS).save(
            PUBLIC / f"icon-{size}.png", optimize=True,
        )

    master.save(
        PUBLIC / "favicon.ico", format="ICO",
        sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)],
    )
    master.save(PUBLIC / "icon.icns", format="ICNS")

    # Opaque canvas for Android masks; the glyph stays inside the 80% safe area.
    maskable = Image.new("RGBA", master.size, "#122C40")
    maskable.alpha_composite(master)
    maskable = maskable.convert("RGB")
    maskable.resize((512, 512), Image.Resampling.LANCZOS).save(
        PUBLIC / "icon-maskable-512.png", optimize=True,
    )
    resources = ROOT / "frontend" / "resources"
    resources.mkdir(exist_ok=True)
    maskable.save(resources / "icon.png", optimize=True)
    for density, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                          ("xxhdpi", 144), ("xxxhdpi", 192)):
        destination = resources / "android" / f"mipmap-{density}"
        destination.mkdir(parents=True, exist_ok=True)
        launcher = maskable.resize((size, size), Image.Resampling.LANCZOS)
        launcher.save(destination / "ic_launcher.png", optimize=True)
        launcher.save(destination / "ic_launcher_round.png", optimize=True)
        foreground_size = size * 108 // 48
        foreground = Image.new("RGBA", (foreground_size, foreground_size), "#122C40")
        artwork_size = round(foreground_size * 0.88)
        artwork = master.resize((artwork_size, artwork_size), Image.Resampling.LANCZOS)
        offset = (foreground_size - artwork_size) // 2
        foreground.alpha_composite(artwork, (offset, offset))
        foreground.save(destination / "ic_launcher_foreground.png", optimize=True)
    print("Exported PNG, ICO, ICNS and Android source icons from icon.svg")


if __name__ == "__main__":
    main()
