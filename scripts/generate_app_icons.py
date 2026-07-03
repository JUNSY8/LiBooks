"""Genera PNG multi-tamaño y app_icon.ico (Windows)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"
SOURCE = ICONS / "app_icon_512.png"

PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)


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
    resampling = Image.Resampling.LANCZOS

    for size in PNG_SIZES:
        if size == 512:
            out = SOURCE
        else:
            out = ICONS / f"app_icon_{size}.png"
            resized = img.resize((size, size), resampling)
            resized.save(out, format="PNG", optimize=True)
            print(f"  {out.relative_to(ROOT)}")

    ico_path = ICONS / "app_icon.ico"
    ico_images = [img.resize((s, s), resampling) for s in ICO_SIZES]
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path.relative_to(ROOT)}")
    _export_web_icons(img, resampling)
    return 0


def _export_web_icons(img, resampling) -> None:
    """Copia iconos web a LiBooks-Web/public si existe el proyecto hermano."""
    web_public = ROOT.parent / "LiBooks-Web" / "public"
    if not web_public.is_dir():
        return

    web_files = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "apple-touch-icon.png": 180,
    }
    for filename, size in web_files.items():
        out = web_public / filename
        resized = img.resize((size, size), resampling)
        resized.save(out, format="PNG", optimize=True)
        print(f"  {out}")

    ico_path = web_public / "favicon.ico"
    ico_images = [
        img.resize((s, s), resampling) for s in (16, 32, 48, 64, 128, 256)
    ]
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path}")


if __name__ == "__main__":
    print("Generando iconos desde app_icon_512.png...")
    raise SystemExit(main())
