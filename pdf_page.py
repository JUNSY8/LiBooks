"""Widget de página PDF con selección, resaltados y resultados de búsqueda."""

import json
import logging
from typing import List, Optional

import fitz
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen
from PyQt5.QtCore import Qt, QRect, pyqtSignal

from pdf_annotations import rects_from_json, widget_rect_to_page, texto_en_rect

logger = logging.getLogger(__name__)

_HIGHLIGHT = QColor(250, 204, 21, 100)
_SEARCH = QColor(74, 222, 169, 90)
_SEARCH_ACTIVE = QColor(74, 222, 169, 200)
_SELECTION = QColor(96, 165, 250, 90)


class PageWidget(QWidget):
    """Representa una página renderizada con capas de anotación."""

    text_selected = pyqtSignal(int, str, str)  # página, texto, rects_json

    def __init__(self, viewer, page_num: int):
        super().__init__()
        self.viewer = viewer
        self.page_num = page_num
        self._pixmap: Optional[QPixmap] = None
        self._highlights: List[list] = []
        self._search_hits: List[list] = []
        self._active_search = None
        self._origin = None
        self._selection = QRect()
        self._selecting = False
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap: Optional[QPixmap]):
        self._pixmap = pixmap
        self.update()

    def set_highlights(self, rects_list: List[list]):
        self._highlights = rects_list
        self.update()

    def set_search_hits(self, rects_list: List[list], active=None):
        self._search_hits = rects_list
        self._active_search = active
        self.update()

    def load_highlights_from_db(self):
        if not self.viewer.libro_id:
            self.set_highlights([])
            return
        from crud import obtener_resaltados_pagina

        rects = []
        for r in obtener_resaltados_pagina(self.viewer.libro_id, self.page_num):
            rects.extend(rects_from_json(r.rects))
        self.set_highlights(rects)

    def _pdf_rect_to_widget(self, rect_coords) -> QRect:
        z = self.viewer.zoom_level
        x0, y0, x1, y1 = rect_coords
        return QRect(
            int(x0 * z), int(y0 * z),
            int((x1 - x0) * z), int((y1 - y0) * z),
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._pixmap and not self._pixmap.isNull():
            p.drawPixmap(0, 0, self._pixmap)
            overlay = self.viewer.get_eye_comfort_overlay()
            if overlay:
                r, g, b, alpha = overlay
                p.fillRect(self.rect(), QColor(r, g, b, alpha))
        else:
            p.fillRect(self.rect(), QColor("#1a2a33"))

        for coords in self._highlights:
            p.fillRect(self._pdf_rect_to_widget(coords), _HIGHLIGHT)

        for coords in self._search_hits:
            if self._active_search and coords == self._active_search:
                p.fillRect(self._pdf_rect_to_widget(coords), _SEARCH_ACTIVE)
            else:
                p.fillRect(self._pdf_rect_to_widget(coords), _SEARCH)

        if self._selecting and not self._selection.isNull():
            p.fillRect(self._selection, _SELECTION)
            pen = QPen(QColor("#60a5fa"))
            pen.setWidth(1)
            p.setPen(pen)
            p.drawRect(self._selection)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.viewer.libro_id:
            self._origin = event.pos()
            self._selection = QRect(self._origin, self._origin)
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting and self._origin is not None:
            self._selection = QRect(self._origin, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self._selecting:
            return
        self._selecting = False
        self.update()
        if not self.viewer.doc or not self.viewer.libro_id:
            return
        if self._selection.width() < 4 or self._selection.height() < 4:
            return
        try:
            page = self.viewer.doc.load_page(self.page_num)
            pdf_rect = widget_rect_to_page(self._selection, self.viewer.zoom_level)
            words = None
            ocr = getattr(self.viewer, "_ocr", None)
            if ocr and ocr.active:
                words = ocr.get_words(self.page_num)
            texto, rects = texto_en_rect(page, pdf_rect, words=words)
            if texto and rects:
                self.text_selected.emit(
                    self.page_num, texto, json.dumps(rects)
                )
        except Exception as e:
            logger.exception("Error en selección de texto: %s", e)
