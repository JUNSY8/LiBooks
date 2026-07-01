"""Vista de biblioteca: continuar leyendo, cuadrícula, lista y drag & drop."""

import logging
from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFontMetrics

from app_settings import get_library_view, set_library_view
from covers import obtener_portada
from crud import ruta_absoluta_libro
from icons import set_button_icon
from i18n import tr
from styles import ACCENT_TEXT, TEXT_SECONDARY

logger = logging.getLogger(__name__)

_LIST_COVER = (52, 72)
_GRID_COVER = (148, 200)
_CONTINUE_COVER = (72, 100)
_CONTINUE_CARD_HEIGHT = 132


class _BookCardBase(QFrame):
    """Tarjeta clickeable con doble clic para abrir."""

    activated = pyqtSignal(int, str)

    def __init__(self, libro_id: int, ruta_pdf: str, parent=None):
        super().__init__(parent)
        self._libro_id = libro_id
        self._ruta_pdf = ruta_pdf
        self.setCursor(Qt.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.activated.emit(self._libro_id, self._ruta_pdf)
        super().mouseDoubleClickEvent(event)


class LibraryPanel(QWidget):
    """Panel principal de libros con vista cuadrícula/lista."""

    open_requested = pyqtSignal(int, str)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_mode = get_library_view()
        self._show_continue = True
        self.setAcceptDrops(True)
        self._build_ui()
        self._apply_view_mode()
        self.retranslate_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        self._continue_card = QFrame()
        self._continue_card.setObjectName("continueReadingCard")
        self._continue_card.setCursor(Qt.PointingHandCursor)
        self._continue_card.setFixedHeight(_CONTINUE_CARD_HEIGHT)
        self._continue_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cr = QHBoxLayout(self._continue_card)
        cr.setContentsMargins(20, 16, 20, 16)
        cr.setSpacing(16)

        self._continue_cover = QLabel()
        self._continue_cover.setObjectName("bookCover")
        self._continue_cover.setFixedSize(*_CONTINUE_COVER)
        self._continue_cover.setAlignment(Qt.AlignCenter)

        cr_text = QVBoxLayout()
        cr_text.setSpacing(6)
        self._continue_label = QLabel()
        self._continue_label.setObjectName("continueReadingLabel")
        self._continue_title = QLabel()
        self._continue_title.setObjectName("continueReadingTitle")
        self._continue_title.setWordWrap(False)
        self._continue_author = QLabel()
        self._continue_author.setObjectName("bookAuthor")
        self._continue_progress = QProgressBar()
        self._continue_progress.setObjectName("readingProgress")
        self._continue_progress.setTextVisible(False)
        self._continue_progress.setFixedHeight(6)
        self._continue_progress_text = QLabel()
        self._continue_progress_text.setObjectName("continueReadingProgress")
        cr_text.addWidget(self._continue_label)
        cr_text.addWidget(self._continue_title)
        cr_text.addWidget(self._continue_author)
        cr_text.addWidget(self._continue_progress)
        cr_text.addWidget(self._continue_progress_text)

        self._continue_btn = QPushButton()
        self._continue_btn.setObjectName("primaryButton")
        self._continue_btn.clicked.connect(self._on_continue_clicked)
        self._continue_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        cr.addWidget(self._continue_cover)
        cr.addLayout(cr_text, 1)
        cr.addWidget(self._continue_btn, 0, Qt.AlignVCenter)
        self._continue_card.hide()
        self._continue_libro_id = 0
        self._continue_ruta = ""

        def continue_dbl(event):
            if event.button() == Qt.LeftButton:
                self._on_continue_clicked()
            QFrame.mouseDoubleClickEvent(self._continue_card, event)

        self._continue_card.mouseDoubleClickEvent = continue_dbl

        root.addWidget(self._continue_card)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self._btn_view_list = QPushButton()
        self._btn_view_list.setObjectName("viewToggleBtn")
        self._btn_view_list.setToolTip(tr("library.view_list"))
        self._btn_view_list.clicked.connect(lambda: self.set_view_mode("list"))
        self._btn_view_grid = QPushButton()
        self._btn_view_grid.setObjectName("viewToggleBtn")
        self._btn_view_grid.setToolTip(tr("library.view_grid"))
        self._btn_view_grid.clicked.connect(lambda: self.set_view_mode("grid"))
        toolbar.addWidget(self._btn_view_list)
        toolbar.addWidget(self._btn_view_grid)
        root.addLayout(toolbar)

        self._stack = QStackedWidget()

        self._list = QListWidget()
        self._list.setObjectName("bookList")
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.itemDoubleClicked.connect(self._on_list_double_click)
        self._stack.addWidget(self._list)

        self._grid_scroll = QScrollArea()
        self._grid_scroll.setObjectName("bookGridScroll")
        self._grid_scroll.setWidgetResizable(True)
        self._grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._grid_host = QWidget()
        self._grid_layout = QGridLayout(self._grid_host)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._grid_scroll.setWidget(self._grid_host)
        self._stack.addWidget(self._grid_scroll)

        root.addWidget(self._stack, 1)

        self._empty = QLabel()
        self._empty.setObjectName("emptyState")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._empty.hide()
        root.addWidget(self._empty, 0, Qt.AlignTop)
        root.addStretch(1)

        self._drop_overlay = QLabel(self)
        self._drop_overlay.setObjectName("dropOverlay")
        self._drop_overlay.setAlignment(Qt.AlignCenter)
        self._drop_overlay.setText(tr("library.drop_hint"))
        self._drop_overlay.hide()
        self._drop_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

    def retranslate_ui(self):
        self._continue_label.setText(tr("library.continue_reading"))
        self._continue_btn.setText(tr("library.continue_btn"))
        self._empty.setText(tr("books.empty_state"))
        self._drop_overlay.setText(tr("library.drop_hint"))
        self._btn_view_list.setToolTip(tr("library.view_list"))
        self._btn_view_grid.setToolTip(tr("library.view_grid"))
        set_button_icon(self._btn_view_list, "list", 18, TEXT_SECONDARY, "")
        set_button_icon(self._btn_view_grid, "grid", 18, TEXT_SECONDARY, "")
        self._update_view_toggle_styles()

    def set_view_mode(self, mode: str):
        if mode not in ("grid", "list"):
            return
        self._view_mode = mode
        set_library_view(mode)
        self._apply_view_mode()

    def _apply_view_mode(self):
        self._stack.setCurrentIndex(0 if self._view_mode == "list" else 1)
        self._update_view_toggle_styles()

    def _update_view_toggle_styles(self):
        list_active = self._view_mode == "list"
        grid_active = self._view_mode == "grid"
        set_button_icon(
            self._btn_view_list, "list", 18,
            ACCENT_TEXT if list_active else TEXT_SECONDARY, "",
        )
        set_button_icon(
            self._btn_view_grid, "grid", 18,
            ACCENT_TEXT if grid_active else TEXT_SECONDARY, "",
        )
        self._btn_view_list.setProperty("active", list_active)
        self._btn_view_grid.setProperty("active", not list_active)
        for btn in (self._btn_view_list, self._btn_view_grid):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_continue_reading(self, libro):
        if not libro or not self._show_continue:
            self._continue_card.hide()
            return
        ruta = ruta_absoluta_libro(libro)
        if not ruta:
            self._continue_card.hide()
            return

        self._continue_libro_id = libro.id_libro
        self._continue_ruta = ruta
        self._continue_titulo_full = libro.titulo or tr("books.no_title")
        self._elide_continue_title(self._continue_titulo_full)
        autor = libro.autor.nombre if getattr(libro, "autor", None) else ""
        self._continue_author.setText(autor or tr("books.unknown_author"))

        px = obtener_portada(libro.id_libro, ruta, *_CONTINUE_COVER)
        self._continue_cover.setPixmap(px)

        total = libro.total_paginas or 0
        leidas = libro.paginas_leidas or 0
        if total > 0:
            pct = min(100, int(leidas / total * 100))
            self._continue_progress.setValue(pct)
            self._continue_progress_text.setText(
                tr("library.progress_pages", current=leidas + 1, total=total, pct=pct)
            )
        else:
            self._continue_progress.setValue(0)
            self._continue_progress_text.setText(tr("library.progress_unknown"))

        self._continue_card.show()

    def load_books(self, libros: List, show_continue: bool = True):
        self._show_continue = show_continue
        self.clear()
        if show_continue:
            from crud import obtener_libro_continuar_lectura
            self.set_continue_reading(obtener_libro_continuar_lectura())
        else:
            self._continue_card.hide()

        for libro in libros:
            self._add_book(libro)

        count = len(libros)
        self._empty.setVisible(count == 0)
        self._stack.setVisible(count > 0)
        return count

    def clear(self):
        self._list.clear()
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def count(self) -> int:
        return self._list.count()

    def _on_continue_clicked(self):
        if self._continue_ruta:
            self.open_requested.emit(self._continue_libro_id, self._continue_ruta)

    def _on_list_double_click(self, item):
        self.open_requested.emit(
            item.data(Qt.UserRole + 1) or 0,
            item.data(Qt.UserRole) or "",
        )

    def _add_book(self, libro):
        ruta = ruta_absoluta_libro(libro)
        if not ruta:
            return
        titulo = libro.titulo or tr("books.no_title")
        autor = libro.autor.nombre if getattr(libro, "autor", None) else tr("books.unknown_author")
        libro_id = libro.id_libro

        self._add_list_item(libro_id, ruta, titulo, autor)
        self._add_grid_item(libro, ruta, titulo, autor)

    def _add_list_item(self, libro_id, ruta, titulo, autor):
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 88))
        item.setData(Qt.UserRole, ruta)
        item.setData(Qt.UserRole + 1, libro_id)

        card = _BookCardBase(libro_id, ruta)
        card.setObjectName("bookCard")
        card.activated.connect(self.open_requested.emit)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        cover = QLabel()
        cover.setObjectName("bookCover")
        cover.setFixedSize(*_LIST_COVER)
        cover.setAlignment(Qt.AlignCenter)
        cover.setPixmap(obtener_portada(libro_id, ruta, *_LIST_COVER))

        info = QVBoxLayout()
        info.setSpacing(4)
        t = QLabel(titulo)
        t.setObjectName("bookTitle")
        t.setWordWrap(True)
        a = QLabel(autor)
        a.setObjectName("bookAuthor")
        info.addWidget(t)
        info.addWidget(a)

        actions = self._action_buttons(libro_id)
        layout.addWidget(cover)
        layout.addLayout(info, 1)
        layout.addLayout(actions)

        self._list.addItem(item)
        self._list.setItemWidget(item, card)

    def _add_grid_item(self, libro, ruta, titulo, autor):
        card = _BookCardBase(libro.id_libro, ruta)
        card.setObjectName("bookGridCard")
        card.setFixedWidth(168)
        card.activated.connect(self.open_requested.emit)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        cover = QLabel()
        cover.setObjectName("bookGridCover")
        cover.setFixedSize(*_GRID_COVER)
        cover.setAlignment(Qt.AlignCenter)
        cover.setPixmap(obtener_portada(libro.id_libro, ruta, *_GRID_COVER))

        t = QLabel(titulo)
        t.setObjectName("bookGridTitle")
        t.setWordWrap(True)
        t.setAlignment(Qt.AlignHCenter)
        a = QLabel(autor)
        a.setObjectName("bookAuthor")
        a.setWordWrap(True)
        a.setAlignment(Qt.AlignHCenter)

        actions = self._action_buttons(libro.id_libro)
        actions.setAlignment(Qt.AlignCenter)

        layout.addWidget(cover, 0, Qt.AlignHCenter)
        layout.addWidget(t)
        layout.addWidget(a)
        layout.addLayout(actions)

        cols = 4
        idx = self._grid_layout.count()
        self._grid_layout.addWidget(card, idx // cols, idx % cols)

    def _action_buttons(self, libro_id: int) -> QHBoxLayout:
        from icons import set_button_icon as sbi

        actions = QHBoxLayout()
        actions.setSpacing(6)
        btn_edit = QPushButton()
        btn_edit.setObjectName("iconButton")
        btn_edit.setToolTip(tr("books.edit_tooltip"))
        sbi(btn_edit, "edit", 18)
        btn_del = QPushButton()
        btn_del.setObjectName("iconButtonDanger")
        btn_del.setToolTip(tr("books.delete_tooltip"))
        sbi(btn_del, "trash", 18)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(libro_id))
        btn_del.clicked.connect(lambda: self.delete_requested.emit(libro_id))
        actions.addWidget(btn_edit)
        actions.addWidget(btn_del)
        return actions

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._continue_card.isVisible() and self._continue_title.text():
            self._elide_continue_title(self._continue_title.text())
        if self._drop_overlay.isVisible():
            self._drop_overlay.setGeometry(self.rect())

    def _elide_continue_title(self, titulo: str):
        fm = QFontMetrics(self._continue_title.font())
        ancho = max(160, self._continue_card.width() - 280)
        self._continue_title.setText(fm.elidedText(titulo, Qt.ElideRight, ancho))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            pdfs = [u for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
            if pdfs:
                event.acceptProposedAction()
                self._drop_overlay.setGeometry(self.rect())
                self._drop_overlay.show()
                self._drop_overlay.raise_()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._drop_overlay.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self._drop_overlay.hide()
        if event.mimeData().hasUrls():
            rutas = [u.toLocalFile() for u in event.mimeData().urls()]
            self.files_dropped.emit(rutas)
            event.acceptProposedAction()
        else:
            event.ignore()
