"""Selector visual de Brillo bibliografico (puntos luminosos circulares)."""

from typing import Optional

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen

from brillo import (
    BRILLO_MAX, BRILLO_DOT_RGB, BRILLO_DOT_INACTIVE_RGB,
    normalizar_brillo, nombre_brillo, descripcion_brillo,
)
from i18n import tr


class BrilloDots(QWidget):
    """Cinco circulos luminosos; clic en el punto N asigna brillo N (repetir quita)."""

    brillo_changed = pyqtSignal(int)

    def __init__(self, compact: bool = False, grid: bool = False, parent=None):
        super().__init__(parent)
        self._nivel = 0
        self._compact = compact and not grid
        self._grid = grid
        if grid:
            self._radius = 6
            self._gap = 7
            self._pad = 2
        else:
            self._radius = 4 if compact else 8
            self._gap = 5 if compact else 10
            self._pad = 2 if compact else 4
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._sync_size()
        self._update_tooltip()

    def _sync_size(self):
        w = self._pad * 2 + BRILLO_MAX * (self._radius * 2) + (BRILLO_MAX - 1) * self._gap
        h = self._pad * 2 + self._radius * 2
        self.setFixedSize(w, h)

    def retranslate_ui(self):
        self._update_tooltip()

    def nivel(self) -> int:
        return self._nivel

    def set_nivel(self, nivel: int, emit: bool = False):
        nivel = normalizar_brillo(nivel)
        if nivel == self._nivel:
            return
        self._nivel = nivel
        self._update_tooltip()
        self.update()
        if emit:
            self.brillo_changed.emit(self._nivel)

    def _dot_centers(self):
        cy = self.height() / 2.0
        x = float(self._pad + self._radius)
        step = self._radius * 2 + self._gap
        return [(x + i * step, cy) for i in range(BRILLO_MAX)]

    def _index_at(self, pos) -> Optional[int]:
        px, py = pos.x(), pos.y()
        for i, (cx, cy) in enumerate(self._dot_centers(), start=1):
            dx, dy = px - cx, py - cy
            hit = self._radius + (3 if self._grid else (2 if self._compact else 4))
            if dx * dx + dy * dy <= hit * hit:
                return i
        return None

    def _tooltip_for_dot(self, index: int) -> str:
        return f"{nombre_brillo(index)}\n{descripcion_brillo(index)}"

    def _update_tooltip(self, hover_index: Optional[int] = None):
        if hover_index is not None:
            self.setToolTip(self._tooltip_for_dot(hover_index))
        elif self._nivel:
            self.setToolTip(
                f"{nombre_brillo(self._nivel)}\n{descripcion_brillo(self._nivel)}"
            )
        else:
            self.setToolTip(tr("brillo.tap_to_rate"))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for i, (cx, cy) in enumerate(self._dot_centers(), start=1):
            activo = self._nivel >= i
            if activo:
                r, g, b = BRILLO_DOT_RGB[i - 1]
                glow = QColor(r, g, b, 55)
                painter.setPen(Qt.NoPen)
                painter.setBrush(glow)
                gr = self._radius + (4 if self._grid else (3 if self._compact else 5))
                painter.drawEllipse(int(cx - gr), int(cy - gr), int(gr * 2), int(gr * 2))
                core = QColor(r, g, b, 230)
            else:
                ir, ig, ib = BRILLO_DOT_INACTIVE_RGB
                core = QColor(ir, ig, ib, 70)
            painter.setPen(QPen(QColor(255, 255, 255, 35 if activo else 18), 1))
            painter.setBrush(core)
            painter.drawEllipse(
                int(cx - self._radius), int(cy - self._radius),
                int(self._radius * 2), int(self._radius * 2),
            )
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
        nuevo = 0 if self._nivel == idx else idx
        self.set_nivel(nuevo, emit=True)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.accept()


class BrilloPicker(QWidget):
    """Selector completo para el dialogo de libro."""

    brillo_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self._lbl_nombre = QLabel()
        self._lbl_nombre.setObjectName("brilloLevelName")
        root.addWidget(self._lbl_nombre)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self._dots = BrilloDots(compact=False)
        self._dots.brillo_changed.connect(self._on_dots_changed)
        self._btn_clear = QPushButton()
        self._btn_clear.setObjectName("ghostButton")
        self._btn_clear.setCursor(Qt.PointingHandCursor)
        self._btn_clear.clicked.connect(lambda: self._dots.set_nivel(0, emit=True))
        row.addWidget(self._dots)
        row.addWidget(self._btn_clear)
        row.addStretch()
        root.addLayout(row)

        self.retranslate_ui()

    def retranslate_ui(self):
        self._btn_clear.setText(tr("brillo.clear"))
        self._dots.retranslate_ui()
        self._refresh_label()

    def nivel(self) -> int:
        return self._dots.nivel()

    def set_nivel(self, nivel: int):
        self._dots.set_nivel(normalizar_brillo(nivel), emit=False)
        self._refresh_label()

    def _on_dots_changed(self, nivel: int):
        self._refresh_label()
        self.brillo_changed.emit(nivel)

    def _refresh_label(self):
        n = self._dots.nivel()
        self._lbl_nombre.setText(nombre_brillo(n))
        self._lbl_nombre.setToolTip(descripcion_brillo(n))