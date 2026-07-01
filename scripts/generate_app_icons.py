"""Genera PNG multi-tamaño, app_icon.ico (Windows) y app_icon.icns (macOS)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"
SOURCE = ICONS / "app_icon_512.png"

PNG_SIZES = (32, 48, 128, 256, 512)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# Tamaños requeridos por iconutil (macOS).
ICNS_ICONSET = (
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
)


def main() -> int:
    if not SOURCE.is_file():
        print(f"No existe la fuente: {SOURCE}", file=sys.stderr)
        return 1

    try:
        from PIL import Image
    except ImportError:
        print("Instala Pillow: pip install pillow", file=sys.stderr)
        return 1

    img = Image.open(SOURCE).convert("RGBA")

    for size in PNG_SIZES:
        if size == 512:
            out = SOURCE
        else:
            out = ICONS / f"app_icon_{size}.png"
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(out, format="PNG", optimize=True)
            print(f"  {out.relative_to(ROOT)}")

    ico_path = ICONS / "app_icon.ico"
    ico_images = [
        img.resize((s, s), Image.Resampling.LANCZOS) for s in ICO_SIZES
    ]
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path.relative_to(ROOT)}")
    return _generate_icns(img, Image.Resampling.LANCZOS)


def _generate_icns(img, resampling) -> int:
    """Genera app_icon.icns en macOS con iconutil; en otros SO solo prepara el iconset."""
    iconset = ICONS / "app_icon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for filename, size in ICNS_ICONSET:
        out = iconset / filename
        resized = img.resize((size, size), resampling)
        resized.save(out, format="PNG", optimize=True)

    icns_path = ICONS / "app_icon.icns"
    if sys.platform == "darwin" and shutil.which("iconutil"):
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
            check=True,
        )
        print(f"  {icns_path.relative_to(ROOT)}")
    else:
        print(
            "  app_icon.iconset listo; ejecuta en macOS: "
            f"iconutil -c icns {iconset.relative_to(ROOT)} -o assets/icons/app_icon.icns"
        )
    return 0


if __name__ == "__main__":
    print("Generando iconos desde app_icon_512.png...")
    raise SystemExit(main())
