"""Genera PNG multi-tamaño y app_icon.ico desde assets/icons/app_icon_512.png."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"
SOURCE = ICONS / "app_icon_512.png"

PNG_SIZES = (32, 48, 128, 256, 512)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


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
    return 0


if __name__ == "__main__":
    print("Generando iconos desde app_icon_512.png...")
    raise SystemExit(main())
