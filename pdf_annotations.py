"""Utilidades de selección y dibujo de anotaciones en páginas PDF."""

import json
from typing import List, Optional, Tuple

import fitz


def rects_to_json(rects: List[list]) -> str:
    return json.dumps(rects)


def rects_from_json(data: str) -> List[list]:
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return []


def widget_rect_to_page(widget_rect, zoom: float) -> fitz.Rect:
    """Convierte un QRect en coordenadas PDF (puntos, zoom 1.0)."""
    x0 = min(widget_rect.left(), widget_rect.right()) / zoom
    y0 = min(widget_rect.top(), widget_rect.bottom()) / zoom
    x1 = max(widget_rect.left(), widget_rect.right()) / zoom
    y1 = max(widget_rect.top(), widget_rect.bottom()) / zoom
    return fitz.Rect(x0, y0, x1, y1)


def texto_en_rect(page: fitz.Page, rect: fitz.Rect,
                  words: Optional[List] = None) -> Tuple[str, List[list]]:
    """Devuelve texto y rectángulos de palabras dentro del área seleccionada."""
    if rect.is_empty or rect.get_area() < 2:
        return "", []
    fuente = words if words is not None else page.get_text("words")
    palabras = []
    rects = []
    for w in fuente:
        wr = fitz.Rect(w[0], w[1], w[2], w[3])
        if wr.intersects(rect):
            palabras.append(w[4])
            rects.append([w[0], w[1], w[2], w[3]])
    return " ".join(palabras).strip(), rects
