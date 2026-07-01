"""Iconos LiBooks — PNG del diseño oficial + fallback vectorial para acciones menores."""

from typing import Optional

from PyQt5.QtCore import Qt, QSize, QPointF, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QPainterPath

from paths import resource_path
from styles import ACCENT, BG_MAIN

# PNG oficiales (assets/icons/)
_PNG = {
    "app": "assets/icons/app_icon_256.png",
    "book": "assets/icons/app_icon_256.png",
    "books": "assets/icons/app_icon_256.png",
    "edit": "assets/icons/icon_editar.png",
    "trash": "assets/icons/icon_eliminar.png",
    "folder": "assets/icons/icon_coleccion.png",
    "collection": "assets/icons/icon_coleccion.png",
}

_APP_BY_SIZE = {
    32: "assets/icons/app_icon_32.png",
    48: "assets/icons/app_icon_48.png",
    128: "assets/icons/app_icon_128.png",
    256: "assets/icons/app_icon_256.png",
}

# Iconos sin PNG: se dibujan con QPainter
_VECTOR_ONLY = frozenset({"settings", "close", "check", "replace", "plus"})


def _png_path(name: str, size: int) -> Optional[str]:
    if name in ("app", "book", "books"):
        best = min(_APP_BY_SIZE, key=lambda s: abs(s - size))
        if abs(best - size) <= best * 0.6:
            return resource_path(_APP_BY_SIZE[best])
        return resource_path(_PNG[name])
    rel = _PNG.get(name)
    return resource_path(rel) if rel else None


def _load_png(name: str, size: int) -> Optional[QPixmap]:
    path = _png_path(name, size)
    if not path:
        return None
    px = QPixmap(path)
    if px.isNull():
        return None
    if px.width() != size or px.height() != size:
        px = px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return px


# ── Fallback vectorial (settings, close, check, replace) ─────────────

def _qcolor(hex_color: str) -> QColor:
    return QColor(hex_color)


def _stroke_pen(color: QColor, width: float, size: int) -> QPen:
    pen = QPen(color)
    pen.setWidthF(max(1.2, width * size / 24))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _canvas(size: int) -> tuple[QPixmap, QPainter]:
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    return px, p


def _scale(size: int, x: float, y: float) -> tuple[float, float]:
    pad = size * 0.12
    return pad + x * (size - 2 * pad) / 24, pad + y * (size - 2 * pad) / 24


def _draw_settings(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.4, size)
    p.setPen(pen)
    cx, cy = _scale(size, 12, 12)
    r = (size - 2 * size * 0.12) * 5 / 24
    p.drawEllipse(QPointF(cx, cy), r, r)
    outer = (size - 2 * size * 0.12) * 10 / 24
    for i in range(8):
        p.save()
        p.translate(cx, cy)
        p.rotate(i * 45)
        p.drawLine(0, int(-outer * 0.55), 0, int(-outer * 0.85))
        p.restore()


def _draw_close(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.8, size)
    p.setPen(pen)
    x7, y7 = _scale(size, 7, 7)
    x17, y17 = _scale(size, 17, 17)
    p.drawLine(int(x7), int(y7), int(x17), int(y17))
    p.drawLine(int(x17), int(y7), int(x7), int(y17))


def _draw_check(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 2.0, size)
    p.setPen(pen)
    x6, y12 = _scale(size, 6, 13)
    x10, y17 = _scale(size, 10, 17)
    x18, y7 = _scale(size, 18, 7)
    path = QPainterPath()
    path.moveTo(x6, y12)
    path.lineTo(x10, y17)
    path.lineTo(x18, y7)
    p.drawPath(path)


def _draw_replace(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.5, size)
    p.setPen(pen)
    cx, cy = _scale(size, 12, 12)
    r = (size - 2 * size * 0.12) * 7 / 24
    p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 50 * 16, 240 * 16)
    ax, ay = _scale(size, 18, 6)
    p.drawLine(int(ax - 3), int(ay + 2), int(ax), int(ay))
    p.drawLine(int(ax), int(ay), int(ax - 1), int(ay + 4))


def _draw_app_logo(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x1, y19 = _scale(size, 3, 19)
    x21, y5 = _scale(size, 21, 5)
    cx, _ = _scale(size, 12, 0)
    _, y5s = _scale(size, 0, 5)
    _, y19s = _scale(size, 0, 19)
    path = QPainterPath()
    path.moveTo(x1, y19)
    path.lineTo(x1, y5s)
    path.quadTo(cx, _scale(size, 12, 3)[1], x21, y5s)
    path.lineTo(x21, y19)
    path.quadTo(cx, _scale(size, 12, 16)[1], x1, y19)
    p.drawPath(path)


_VECTOR_DRAWERS = {
    "settings": _draw_settings,
    "close": _draw_close,
    "check": _draw_check,
    "replace": _draw_replace,
}


def _draw_vector(name: str, size: int, color: Optional[str]) -> QPixmap:
    drawer = _VECTOR_DRAWERS.get(name)
    if not drawer:
        drawer = _draw_app_logo
    col = _qcolor(color or ACCENT)
    px, p = _canvas(size)
    drawer(p, size, col)
    p.end()
    return px


def pixmap(name: str, size: int = 24, color: Optional[str] = None) -> QPixmap:
    """Devuelve el icono escalado al tamaño indicado."""
    if name not in _VECTOR_ONLY:
        px = _load_png(name, size)
        if px is not None:
            return px
    return _draw_vector(name, size, color)


def icon(name: str, size: int = 24, color: Optional[str] = None) -> QIcon:
    return QIcon(pixmap(name, size, color))


def app_icon() -> QIcon:
    """Icono de ventana — usa los PNG en 32/48/128/256 px."""
    ico = QIcon()
    for sz, rel in sorted(_APP_BY_SIZE.items()):
        path = resource_path(rel)
        px = QPixmap(path)
        if not px.isNull():
            ico.addPixmap(px)
    if ico.isNull():
        ico = QIcon(pixmap("app", 256))
    return ico


def icon_label(name: str, size: int = 20, color: Optional[str] = None):
    from PyQt5.QtWidgets import QLabel

    lbl = QLabel()
    lbl.setPixmap(pixmap(name, size, color))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("background: transparent;")
    lbl.setFixedSize(size + 4, size + 4)
    return lbl


def set_button_icon(
    button,
    name: str,
    size: int = 18,
    color: Optional[str] = None,
    text: Optional[str] = None,
):
    button.setIcon(icon(name, size, color))
    button.setIconSize(QSize(size, size))
    if text is not None:
        button.setText(text)
