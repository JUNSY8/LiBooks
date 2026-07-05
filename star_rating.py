"""Selector visual de valoracion por estrellas (1-5)."""

from typing import Optional

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor

from rating import RATING_MAX, STAR_ACTIVE_RGB, STAR_INACTIVE_RGB, normalizar_rating, etiqueta_rating
from i18n import tr


class StarRatingWidget(QWidget):
    """Cinco estrellas; clic en la estrella N asigna valoracion N."""

    rating_changed = pyqtSignal(int)

    def __init__(self, compact: bool = False, grid: bool = False, parent=None):
        super().__init__(parent)
        self._rating = 0
        self._compact = compact and not grid
        self._grid = grid
        if grid:
            self._star_size = 14
            self._gap = 3
        elif compact:
            self._star_size = 11
            self._gap = 2
        else:
            self._star_size = 18
            self._gap = 4
        self._pad = 2
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._sync_size()
        self._update_tooltip()

    def _sync_size(self):
        w = self._pad * 2 + RATING_MAX * self._star_size + (RATING_MAX - 1) * self._gap
        h = self._pad * 2 + self._star_size + 4
        self.setFixedSize(w, h)

    def retranslate_ui(self):
        self._update_tooltip()

    def rating(self) -> int:
        return self._rating

    def set_rating(self, rating: int, emit: bool = False):
        rating = normalizar_rating(rating)
        if rating == self._rating:
            return
        self._rating = rating
        self._update_tooltip()
        self.update()
        if emit:
            self.rating_changed.emit(self._rating)

    def _star_rects(self):
        rects = []
        x = float(self._pad)
        y = float(self._pad + 2)
        for _ in range(RATING_MAX):
            rects.append((x, y, float(self._star_size), float(self._star_size)))
            x += self._star_size + self._gap
        return rects

    def _index_at(self, pos) -> Optional[int]:
        px, py = pos.x(), pos.y()
        for i, (x, y, w, h) in enumerate(self._star_rects(), start=1):
            if x - 2 <= px <= x + w + 2 and y - 2 <= py <= y + h + 2:
                return i
        return None

    def _update_tooltip(self, hover_index: Optional[int] = None):
        if hover_index is not None:
            self.setToolTip(etiqueta_rating(hover_index))
        elif self._rating:
            self.setToolTip(etiqueta_rating(self._rating))
        else:
            self.setToolTip(tr("rating.tap_to_rate"))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        font = QFont()
        font.setPointSizeF(self._star_size * 0.72)
        painter.setFont(font)
        for i, (x, y, w, h) in enumerate(self._star_rects(), start=1):
            activo = self._rating >= i
            if activo:
                r, g, b = STAR_ACTIVE_RGB
            else:
                r, g, b = STAR_INACTIVE_RGB
            painter.setPen(QColor(r, g, b))
            painter.drawText(int(x), int(y + h - 2), "\u2605")
        painter.end()

    def mouseMoveEvent(self, event):
        idx = self._index_at(event.pos())
        self._update_tooltip(hover_index=idx)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._update_tooltip()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        idx = self._index_at(event.pos())
        if idx is None:
            return
        self.set_rating(idx, emit=True)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.accept()


class StarRatingPicker(QWidget):
    """Selector completo para el dialogo de libro."""

    rating_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self._lbl_value = QLabel()
        self._lbl_value.setObjectName("ratingLevelLabel")
        root.addWidget(self._lbl_value)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self._stars = StarRatingWidget(compact=False)
        self._stars.rating_changed.connect(self._on_stars_changed)
        self._btn_clear = QPushButton()
        self._btn_clear.setObjectName("ghostButton")
        self._btn_clear.setCursor(Qt.PointingHandCursor)
        self._btn_clear.clicked.connect(lambda: self._stars.set_rating(0, emit=True))
        row.addWidget(self._stars)
        row.addWidget(self._btn_clear)
        row.addStretch()
        root.addLayout(row)

        self.retranslate_ui()

    def retranslate_ui(self):
        self._btn_clear.setText(tr("rating.clear"))
        self._stars.retranslate_ui()
        self._refresh_label()

    def rating(self) -> int:
        return self._stars.rating()

    def set_rating(self, rating: int):
        self._stars.set_rating(normalizar_rating(rating), emit=False)
        self._refresh_label()

    def _on_stars_changed(self, rating: int):
        self._refresh_label()
        self.rating_changed.emit(rating)

    def _refresh_label(self):
        self._lbl_value.setText(etiqueta_rating(self._stars.rating()))