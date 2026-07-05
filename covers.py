"""Generación y caché de portadas (miniatura de la 1.ª página)."""

import logging
import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from paths import user_data_dir

logger = logging.getLogger(__name__)

COVERS_DIR = os.path.join(user_data_dir(), "covers")
os.makedirs(COVERS_DIR, exist_ok=True)

_PLACEHOLDER: Optional[QPixmap] = None


def _cover_file(libro_id: int) -> str:
    return os.path.join(COVERS_DIR, f"{libro_id}.png")


def generar_portada(ruta_pdf: str, libro_id: int, ancho: int = 280) -> bool:
    """Renderiza la 1.ª página y la guarda en caché. Devuelve True si tuvo éxito."""
    try:
        import fitz

        with fitz.open(ruta_pdf) as doc:
            if doc.page_count == 0:
                return False
            page = doc.load_page(0)
            rect = page.rect
            escala = ancho / rect.width if rect.width else 1.0
            mat = fitz.Matrix(escala, escala)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(_cover_file(libro_id))
            return True
    except Exception as e:
        logger.warning("No se pudo generar portada para libro %s: %s", libro_id, e)
        return False


def placeholder_cover(ancho: int, alto: int) -> QPixmap:
    """Portada genérica para libros con contenido oculto."""
    return _placeholder(ancho, alto)


def _placeholder(ancho: int, alto: int) -> QPixmap:
    global _PLACEHOLDER
    from icons import pixmap as icon_pixmap

    px = icon_pixmap("book", min(ancho, alto) - 8)
    result = QPixmap(ancho, alto)
    result.fill(Qt.transparent)
    from PyQt5.QtGui import QPainter

    p = QPainter(result)
    x = (ancho - px.width()) // 2
    y = (alto - px.height()) // 2
    p.drawPixmap(x, y, px)
    p.end()
    return result


def obtener_portada(
    libro_id: int,
    ruta_pdf: str,
    ancho: int,
    alto: int,
) -> QPixmap:
    """Devuelve la portada escalada; genera caché bajo demanda."""
    path = _cover_file(libro_id)
    if not os.path.isfile(path) and ruta_pdf and os.path.exists(ruta_pdf):
        generar_portada(ruta_pdf, libro_id, ancho=max(ancho * 2, 200))

    if os.path.isfile(path):
        px = QPixmap(path)
        if not px.isNull():
            scaled = px.scaled(
                ancho, alto, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            scaled.setDevicePixelRatio(1.0)
            return scaled

    return _placeholder(ancho, alto)


def eliminar_portada(libro_id: int) -> None:
    path = _cover_file(libro_id)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("No se pudo eliminar portada %s: %s", path, e)
