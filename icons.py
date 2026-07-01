"""Iconos LiBooks — PNG del diseño oficial + fallback vectorial para acciones menores."""

import os
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
    "add_book": "assets/icons/icon_coleccion.png",
}

_APP_BY_SIZE = {
    16: "assets/icons/app_icon_16.png",
    24: "assets/icons/app_icon_24.png",
    32: "assets/icons/app_icon_32.png",
    48: "assets/icons/app_icon_48.png",
    64: "assets/icons/app_icon_64.png",
    128: "assets/icons/app_icon_128.png",
    256: "assets/icons/app_icon_256.png",
    512: "assets/icons/app_icon_512.png",
}

# Iconos sin PNG: se dibujan con QPainter
_VECTOR_ONLY = frozenset({
    "settings", "close", "check", "replace", "plus", "list", "grid",
    "search", "highlight", "reading", "sidebar", "fullscreen",
    "chart", "export",
})


def _png_path(name: str, size: int) -> Optional[str]:
    if name in ("app", "book", "books"):
        best = min(_APP_BY_SIZE, key=lambda s: abs(s - size))
        if abs(best - size) <= best * 0.6:
            return resource_path(_APP_BY_SIZE[best])
        return resource_path(_PNG[name])
    rel = _PNG.get(name)
    return resource_path(rel) if rel else None


def _recolor_pixmap(px: QPixmap, color: str) -> QPixmap:
    """Sustituye el color del PNG por el indicado (p. ej. icono oscuro sobre fondo accent)."""
    result = QPixmap(px.size())
    result.fill(Qt.transparent)
    p = QPainter(result)
    p.setCompositionMode(QPainter.CompositionMode_Source)
    p.drawPixmap(0, 0, px)
    p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.fillRect(result.rect(), _qcolor(color))
    p.end()
    return result


def _load_png(name: str, size: int, color: Optional[str] = None) -> Optional[QPixmap]:
    path = _png_path(name, size)
    if not path:
        return None
    px = QPixmap(path)
    if px.isNull():
        return None
    if px.width() != size or px.height() != size:
        px = px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if color:
        px = _recolor_pixmap(px, color)
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


def _draw_folder(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x4, y8 = _scale(size, 4, 8)
    x9, y5 = _scale(size, 9, 5)
    x20, y5 = _scale(size, 20, 5)
    x20, y19 = _scale(size, 20, 19)
    x4, y19 = _scale(size, 4, 19)
    path = QPainterPath()
    path.moveTo(x4, y8)
    path.lineTo(x9, y5)
    path.lineTo(x20, y5)
    path.lineTo(x20, y19)
    path.lineTo(x4, y19)
    path.closeSubpath()
    p.drawPath(path)


def _draw_list(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x5, y6 = _scale(size, 5, 6)
    x19, y6 = _scale(size, 19, 6)
    x19, y18 = _scale(size, 19, 18)
    x5, y18 = _scale(size, 5, 18)
    p.drawLine(int(x5), int(y6), int(x19), int(y6))
    for y in (10, 14, 18):
        _, yy = _scale(size, 0, y)
        x7, _ = _scale(size, 7, 0)
        x17, _ = _scale(size, 17, 0)
        p.drawLine(int(x7), int(yy), int(x17), int(yy))


def _draw_grid(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    for col, row in ((4, 4), (14, 4), (4, 14), (14, 14)):
        x, y = _scale(size, col, row)
        x2, y2 = _scale(size, col + 6, row + 6)
        path = QPainterPath()
        path.addRoundedRect(QRectF(x, y, x2 - x, y2 - y), 1.5, 1.5)
        p.drawPath(path)


def _draw_search(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    cx, cy = _scale(size, 10, 10)
    r = (size - 2 * size * 0.12) * 5 / 24
    p.drawEllipse(QPointF(cx, cy), r, r)
    x14, y14 = _scale(size, 14, 14)
    x19, y19 = _scale(size, 19, 19)
    p.drawLine(int(x14), int(y14), int(x19), int(y19))


def _draw_highlight(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 2.2, size)
    p.setPen(pen)
    x4, y14 = _scale(size, 4, 14)
    x20, y14 = _scale(size, 20, 14)
    p.drawLine(int(x4), int(y14), int(x20), int(y14))


def _draw_reading(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x5, y6 = _scale(size, 5, 6)
    x19, y6 = _scale(size, 19, 6)
    x19, y18 = _scale(size, 19, 18)
    x5, y18 = _scale(size, 5, 18)
    path = QPainterPath()
    path.moveTo(x5, y6)
    path.lineTo(x19, y6)
    path.lineTo(x19, y18)
    path.lineTo(x5, y18)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(int(_scale(size, 8, 10)[0]), int(_scale(size, 8, 10)[1]),
               int(_scale(size, 16, 10)[0]), int(_scale(size, 16, 10)[1]))


def _draw_sidebar(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x5, y5 = _scale(size, 5, 5)
    x11, y5 = _scale(size, 11, 5)
    x11, y19 = _scale(size, 11, 19)
    x5, y19 = _scale(size, 5, 19)
    path = QPainterPath()
    path.moveTo(x5, y5)
    path.lineTo(x11, y5)
    path.lineTo(x11, y19)
    path.lineTo(x5, y19)
    path.closeSubpath()
    p.drawPath(path)
    x14, _ = _scale(size, 14, 0)
    x19, _ = _scale(size, 19, 0)
    for y in (8, 12, 16):
        _, yy = _scale(size, 0, y)
        p.drawLine(int(x14), int(yy), int(x19), int(yy))


def _draw_chart(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    p.setBrush(QBrush(color))
    for x_off, h in ((6, 8), (11, 14), (16, 10)):
        x, y_base = _scale(size, x_off, 18)
        _, y_top = _scale(size, x_off, 18 - h)
        w = size * 3 / 24
        p.drawRect(int(x), int(y_top), int(w), int(y_base - y_top))


def _draw_export(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x7, y5 = _scale(size, 7, 5)
    x17, y5 = _scale(size, 17, 5)
    x17, y15 = _scale(size, 17, 15)
    x7, y15 = _scale(size, 7, 15)
    path = QPainterPath()
    path.moveTo(x7, y5)
    path.lineTo(x17, y5)
    path.lineTo(x17, y15)
    path.lineTo(x7, y15)
    path.closeSubpath()
    p.drawPath(path)
    cx, y16 = _scale(size, 12, 16)
    _, y20 = _scale(size, 12, 20)
    p.drawLine(int(cx), int(y16), int(cx), int(y20))
    x9, y18 = _scale(size, 9, 18)
    x15, y18 = _scale(size, 15, 18)
    p.drawLine(int(x9), int(y18), int(cx), int(y20))
    p.drawLine(int(cx), int(y20), int(x15), int(y18))


def _draw_fullscreen(p: QPainter, size: int, color: QColor):
    pen = _stroke_pen(color, 1.6, size)
    p.setPen(pen)
    x5, y5 = _scale(size, 5, 5)
    x14, y5 = _scale(size, 14, 5)
    x14, y14 = _scale(size, 14, 14)
    x5, y14 = _scale(size, 5, 14)
    p.drawLine(int(x5), int(y5), int(x14), int(y5))
    p.drawLine(int(x14), int(y5), int(x14), int(y14))
    p.drawLine(int(x14), int(y14), int(x5), int(y14))
    p.drawLine(int(x5), int(y14), int(x5), int(y5))
    x10, y10 = _scale(size, 10, 10)
    x19, y10 = _scale(size, 19, 10)
    x19, y19 = _scale(size, 19, 19)
    x10, y19 = _scale(size, 10, 19)
    p.drawLine(int(x10), int(y10), int(x19), int(y10))
    p.drawLine(int(x19), int(y10), int(x19), int(y19))
    p.drawLine(int(x19), int(y19), int(x10), int(y19))
    p.drawLine(int(x10), int(y19), int(x10), int(y10))


_VECTOR_DRAWERS = {
    "settings": _draw_settings,
    "close": _draw_close,
    "check": _draw_check,
    "replace": _draw_replace,
    "folder": _draw_folder,
    "collection": _draw_folder,
    "book": _draw_app_logo,
    "books": _draw_app_logo,
    "list": _draw_list,
    "grid": _draw_grid,
    "search": _draw_search,
    "highlight": _draw_highlight,
    "reading": _draw_reading,
    "sidebar": _draw_sidebar,
    "fullscreen": _draw_fullscreen,
    "chart": _draw_chart,
    "export": _draw_export,
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
    if color is not None and name in _VECTOR_DRAWERS:
        return _draw_vector(name, size, color)
    if name not in _VECTOR_ONLY:
        px = _load_png(name, size, color)
        if px is not None:
            return px
    return _draw_vector(name, size, color)


def icon(name: str, size: int = 24, color: Optional[str] = None) -> QIcon:
    return QIcon(pixmap(name, size, color))


def app_icon() -> QIcon:
    """Icono de ventana — usa el .ico multi-resolución cuando está disponible."""
    ico_path = resource_path("assets/icons/app_icon.ico")
    if os.path.isfile(ico_path):
        ico = QIcon(ico_path)
        if not ico.isNull():
            return ico

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
