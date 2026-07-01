"""Panel de estadísticas de lectura."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)
from PyQt5.QtCore import Qt

from crud import obtener_estadisticas_lectura, ruta_absoluta_libro
from i18n import tr, register_language_callback


class StatsPanel(QWidget):
    """Métricas simples de la biblioteca."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = {}
        self._recent_host = QVBoxLayout()
        self._build_ui()
        register_language_callback(self.retranslate_ui)
        self.retranslate_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(20)

        self._title = QLabel()
        self._title.setObjectName("statsTitle")
        root.addWidget(self._title)

        self._subtitle = QLabel()
        self._subtitle.setObjectName("statsSubtitle")
        root.addWidget(self._subtitle)

        grid = QGridLayout()
        grid.setSpacing(12)
        keys = (
            "total_libros", "en_progreso", "completados",
            "sin_leer", "paginas_leidas", "activos_mes",
        )
        for i, key in enumerate(keys):
            card = self._make_stat_card(key)
            self._cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
        root.addLayout(grid)

        self._recent_title = QLabel()
        self._recent_title.setObjectName("fieldLabel")
        root.addWidget(self._recent_title)

        recent_frame = QFrame()
        recent_frame.setObjectName("statsRecentList")
        self._recent_host = QVBoxLayout(recent_frame)
        self._recent_host.setContentsMargins(16, 12, 16, 12)
        self._recent_host.setSpacing(8)
        root.addWidget(recent_frame)
        root.addStretch()

    def _make_stat_card(self, key: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)
        value = QLabel("0")
        value.setObjectName("statValue")
        value.setProperty("statKey", key)
        label = QLabel()
        label.setObjectName("statLabel")
        label.setProperty("statKey", key)
        label.setWordWrap(True)
        lay.addWidget(value)
        lay.addWidget(label)
        card._value_lbl = value
        card._label_lbl = label
        return card

    def retranslate_ui(self):
        self._title.setText(tr("stats.title"))
        self._subtitle.setText(tr("stats.subtitle"))
        self._recent_title.setText(tr("stats.recent_title"))
        labels = {
            "total_libros": tr("stats.total_books"),
            "en_progreso": tr("stats.in_progress"),
            "completados": tr("stats.completed"),
            "sin_leer": tr("stats.unread"),
            "paginas_leidas": tr("stats.pages_read"),
            "activos_mes": tr("stats.active_month"),
        }
        for key, card in self._cards.items():
            card._label_lbl.setText(labels.get(key, key))

    def refresh(self):
        data = obtener_estadisticas_lectura()
        for key, card in self._cards.items():
            card._value_lbl.setText(str(data.get(key, 0)))

        while self._recent_host.count():
            item = self._recent_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recientes = data.get("recientes") or []
        if not recientes:
            empty = QLabel(tr("stats.no_recent"))
            empty.setObjectName("statsEmpty")
            self._recent_host.addWidget(empty)
            return

        for libro in recientes:
            if not ruta_absoluta_libro(libro):
                continue
            row = QHBoxLayout()
            title = QLabel(libro.titulo or tr("books.no_title"))
            title.setObjectName("statsRecentTitle")
            meta = QLabel(self._meta_libro(libro))
            meta.setObjectName("statsRecentMeta")
            meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(title, 1)
            row.addWidget(meta)
            wrap = QWidget()
            wrap.setLayout(row)
            self._recent_host.addWidget(wrap)

    def _meta_libro(self, libro) -> str:
        leidas = libro.paginas_leidas or 0
        total = libro.total_paginas or 0
        if total > 0:
            pct = int(100 * leidas / total)
            return tr("stats.recent_progress", current=leidas, total=total, pct=pct)
        if leidas > 0:
            return tr("library.progress_unknown")
        return tr("stats.not_started")
