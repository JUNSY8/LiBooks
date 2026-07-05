"""Genera PNG multi-tamano y app_icon.ico (Windows) desde el render vectorial."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"

PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
ICO_SIZES = (16, 32, 48, 64, 128, 256, 512)

_SPINE = (150, 245, 210, 255)
_SHADOW = (4, 16, 20, 110)
_BG = (16, 36, 44, 255)
_BG_DEEP = (10, 24, 30, 255)
_RING = (30, 68, 80, 255)
_BOOK_LEFT = (12, 92, 73, 255)
_BOOK_MID = (28, 156, 120, 255)
_BOOK_RIGHT = (70, 224, 180, 255)
_SHELF = (8, 61, 49, 255)


def _px(size: int, frac: float) -> int:
    return max(0, round(size * frac))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _book_polygon(size, cx, bottom, width, height, lean):
    w = width * size
    h = height * size
    cx_px = cx * size
    bottom_px = bottom * size
    top_px = bottom_px - h
    lean_px = lean * w
    half = w / 2
    return [
        (round(cx_px - half + lean_px), round(top_px)),
        (round(cx_px + half + lean_px), round(top_px)),
        (round(cx_px + half - lean_px), round(bottom_px)),
        (round(cx_px - half - lean_px), round(bottom_px)),
    ]


def _draw_spine_lines(draw, poly, count, width):
    if count <= 0 or width <= 0:
        return
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    left_x, right_x = min(xs), max(xs)
    top_y, bottom_y = min(ys), max(ys)
    height = bottom_y - top_y
    if height < 4:
        return
    inset_top = height * 0.12
    inset_bottom = height * 0.18
    usable = height - inset_top - inset_bottom
    for i in range(count):
        t = (i + 1) / (count + 1)
        y = round(top_y + inset_top + usable * t)
        x1 = round(_lerp(left_x, right_x, 0.22))
        x2 = round(_lerp(left_x, right_x, 0.78))
        draw.line([(x1, y), (x2, y)], fill=_SPINE, width=width)


def render_app_icon(size: int) -> Image.Image:
    """Dibuja el icono a tamano nativo (esquinas redondeadas, fondo transparente)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, round(size * 0.06))
    radius = max(2, round(size * 0.19))
    card = (pad, pad, size - pad - 1, size - pad - 1)
    draw.rounded_rectangle(card, radius=radius, fill=_BG)

    if size >= 40:
        ring_w = max(1, round(size * 0.012))
        draw.rounded_rectangle(card, radius=radius, outline=_RING, width=ring_w)

    if size >= 64:
        inner_pad = max(2, round(size * 0.035))
        inner = (
            card[0] + inner_pad,
            card[1] + inner_pad,
            card[2] - inner_pad,
            card[3] - inner_pad,
        )
        draw.rounded_rectangle(inner, radius=max(1, radius - inner_pad), fill=_BG_DEEP)

    shelf_y = 0.70
    shelf_h = 0.045 if size >= 32 else 0.06
    book_h = 0.34 if size >= 32 else 0.38
    book_w = 0.13 if size >= 32 else 0.15

    if size >= 24:
        shadow_y = _px(size, shelf_y + 0.02)
        shadow_h = max(1, round(size * 0.035))
        shadow_w = round(size * 0.52)
        cx = size // 2
        draw.ellipse(
            (cx - shadow_w // 2, shadow_y, cx + shadow_w // 2, shadow_y + shadow_h),
            fill=_SHADOW,
        )

    books = (
        (0.36, book_w, book_h, -0.10, _BOOK_LEFT, 2),
        (0.50, book_w * 0.95, book_h * 1.04, 0.0, _BOOK_MID, 3),
        (0.64, book_w, book_h * 0.98, 0.12, _BOOK_RIGHT, 2),
    )

    spine_w = spine_count = 0
    if size >= 128:
        spine_w, spine_count = max(2, round(size * 0.008)), 3
    elif size >= 64:
        spine_w, spine_count = max(1, round(size * 0.012)), 2
    elif size >= 48:
        spine_w, spine_count = 1, 1

    for cx, bw, bh, lean, color, default_lines in books:
        poly = _book_polygon(size, cx, shelf_y, bw, bh, lean)
        draw.polygon(poly, fill=color)
        lines = default_lines if size >= 128 else (spine_count or (1 if size >= 32 else 0))
        _draw_spine_lines(draw, poly, lines, spine_w)

    draw.rectangle(
        (_px(size, 0.22), _px(size, shelf_y - 0.008), _px(size, 0.78), _px(size, shelf_y + shelf_h)),
        fill=_SHELF,
    )

    if size >= 96:
        highlight_h = max(1, round(size * 0.025))
        for cx, bw, *_ in books:
            w = bw * size
            cx_px = round(cx * size)
            top_y = _px(size, shelf_y - book_h) + max(1, round(size * 0.02))
            draw.rounded_rectangle(
                (cx_px - round(w * 0.22), top_y, cx_px + round(w * 0.22), top_y + highlight_h),
                radius=max(1, highlight_h // 2),
                fill=(255, 255, 255, 38),
            )

    return img


def main() -> int:
    try:
        from PIL import Image as _Image  # noqa: F401 — comprobar Pillow
    except ImportError:
        print("Instala Pillow: pip install pillow", file=sys.stderr)
        return 1

    ICONS.mkdir(parents=True, exist_ok=True)

    rendered: dict[int, Image.Image] = {}
    for size in PNG_SIZES:
        img = render_app_icon(size)
        rendered[size] = img
        out = ICONS / f"app_icon_{size}.png"
        img.save(out, format="PNG", optimize=True)
        print(f"  {out.relative_to(ROOT)}")

    ico_path = ICONS / "app_icon.ico"
    ico_images = [rendered[s] for s in sorted(ICO_SIZES, reverse=True)]
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[im.size for im in ico_images],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path.relative_to(ROOT)}")

    _export_web_icons(rendered)
    _verify_assets()
    return 0


def _export_web_icons(rendered: dict) -> None:
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
        img = rendered.get(size) or render_app_icon(size)
        img.save(out, format="PNG", optimize=True)
        print(f"  {out}")

    ico_path = web_public / "favicon.ico"
    ico_images = [rendered[s] for s in sorted(ICO_SIZES, reverse=True)]
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=[im.size for im in ico_images],
        append_images=ico_images[1:],
    )
    print(f"  {ico_path}")


def _verify_assets() -> None:
    missing = []
    for size in PNG_SIZES:
        if not (ICONS / f"app_icon_{size}.png").is_file():
            missing.append(f"app_icon_{size}.png")
    if not (ICONS / "app_icon.ico").is_file():
        missing.append("app_icon.ico")
    if missing:
        raise SystemExit(f"Faltan assets: {', '.join(missing)}")


if __name__ == "__main__":
    print("Generando iconos LiBooks (render nativo por tamano)...")
    raise SystemExit(main())
