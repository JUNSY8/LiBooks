"""Tour guiado contextual con callouts no bloqueantes."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from PyQt5.QtCore import Qt, QTimer, QEvent, QObject
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_settings import (
    get_help_tips_enabled,
    is_tour_section_seen,
    mark_tour_section_seen,
)
from i18n import tr
from message_boxes import disable_button_default, wire_dialog_buttons
from styles import tour_callout_stylesheet

_active_tour: Optional["SectionTour"] = None


@dataclass
class TourStepDef:
    resolve_widget: Callable[[Any], Optional[QWidget]]
    title_key: str
    body_key: str
    prepare: Optional[Callable[[Any], None]] = None


def _nav_widget(host, key: str) -> Optional[QWidget]:
    buttons = getattr(host, "_nav_buttons", None)
    if not buttons:
        return None
    return buttons.get(key)


def _pdf_tab_bar(host) -> Optional[QWidget]:
    sidebar = getattr(host, "_sidebar", None)
    if sidebar is None:
        return None
    tabs = getattr(sidebar, "tabs", None)
    if tabs is None:
        return None
    return tabs.tabBar()


def _stats_grid(host) -> Optional[QWidget]:
    panel = getattr(host, "_stats_panel", None)
    if panel is None:
        return None
    cards = getattr(panel, "_cards", None)
    if cards:
        return cards.get("total_libros")
    return panel


def _book_edit_file_or_author(host) -> Optional[QWidget]:
    btn = getattr(host, "_btn_reemplazar", None)
    if btn is not None and btn.isVisible():
        return btn
    return getattr(host, "autor_input", None)




def _library_inline_stars(host) -> Optional[QWidget]:
    library = getattr(host, "library", None)
    if library is None:
        return None
    try:
        from star_rating import StarRatingWidget
    except ImportError:
        return None
    for widget in library.findChildren(StarRatingWidget):
        if widget.isVisible():
            return widget
    return None



def _settings_scroll_to(host, widget) -> None:
    scroll = getattr(host, "_scroll", None)
    if scroll is not None and widget is not None:
        scroll.ensureWidgetVisible(widget, 48)


def _settings_prepare_backup(host) -> None:
    _settings_scroll_to(host, getattr(host, "_backup_hint", None))


def _settings_prepare_sync(host) -> None:
    _settings_scroll_to(host, getattr(host, "_sync_hint", None))


def _pdf_ocr_widget(host) -> Optional[QWidget]:
    banner = getattr(host, "_ocr_banner", None)
    if banner is not None and banner.isVisible():
        return banner
    return getattr(host, "search_input", None)


def _settings_form_steps() -> List[TourStepDef]:
    return [
        TourStepDef(
            lambda h: getattr(h, "_backup_hint", None),
            "tour.settings.backup_title",
            "tour.settings.backup_body",
            prepare=_settings_prepare_backup,
        ),
        TourStepDef(
            lambda h: getattr(h, "_sync_hint", None),
            "tour.settings.sync_overview_title",
            "tour.settings.sync_overview_body",
            prepare=_settings_prepare_sync,
        ),
        TourStepDef(
            lambda h: getattr(h, "_sync_enabled", None),
            "tour.settings.sync_enable_title",
            "tour.settings.sync_enable_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_folder", None),
            "tour.settings.sync_folder_title",
            "tour.settings.sync_folder_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_pass_input", None),
            "tour.settings.sync_passphrase_title",
            "tour.settings.sync_passphrase_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_sync_now", None),
            "tour.settings.sync_actions_title",
            "tour.settings.sync_actions_body",
        ),
    ]

def _collection_form_steps() -> List[TourStepDef]:
    return [
        TourStepDef(
            lambda h: getattr(h, "titulo_input", None),
            "tour.collection.name_title",
            "tour.collection.name_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "buscar_input", None),
            "tour.collection.search_title",
            "tour.collection.search_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "libros_list", None),
            "tour.collection.books_title",
            "tour.collection.books_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "autor_combo", None),
            "tour.collection.filters_title",
            "tour.collection.filters_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_crear", None),
            "tour.collection.save_title",
            "tour.collection.save_body",
        ),
    ]


SECTION_STEPS: dict[str, List[TourStepDef]] = {
    "navigation": [
        TourStepDef(
            lambda h: _nav_widget(h, "libros"),
            "tour.nav.books_title",
            "tour.nav.books_body",
        ),
        TourStepDef(
            lambda h: _nav_widget(h, "stats"),
            "tour.nav.stats_title",
            "tour.nav.stats_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_add_col", None),
            "tour.nav.collections_title",
            "tour.nav.collections_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_settings", None),
            "tour.nav.settings_title",
            "tour.nav.settings_body",
        ),
    ],
    "library": [
        TourStepDef(
            lambda h: getattr(h, "search_bar", None),
            "tour.library.search_title",
            "tour.library.search_body",
            prepare=lambda h: h.mostrar_todos_los_libros(),
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_add", None),
            "tour.library.add_title",
            "tour.library.add_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_import_folder", None),
            "tour.library.import_folder_title",
            "tour.library.import_folder_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_combo_sort", None),
            "tour.library.sort_title",
            "tour.library.sort_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_combo_filter", None),
            "tour.library.filter_title",
            "tour.library.filter_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_combo_tag", None),
            "tour.library.tag_title",
            "tour.library.tag_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_combo_rating", None),
            "tour.library.rating_title",
            "tour.library.rating_body",
        ),
        TourStepDef(
            _library_inline_stars,
            "tour.library.stars_title",
            "tour.library.stars_body",
        ),
        TourStepDef(
            lambda h: getattr(getattr(h, "library", None), "_btn_view_grid", None),
            "tour.library.view_title",
            "tour.library.view_body",
        ),
    ],
    "stats": [
        TourStepDef(
            _stats_grid,
            "tour.stats.overview_title",
            "tour.stats.overview_body",
            prepare=lambda h: h.mostrar_estadisticas(),
        ),
    ],
    "collections": [
        TourStepDef(
            lambda h: getattr(h, "_btn_add_col", None),
            "tour.collections.create_title",
            "tour.collections.create_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_collections_scroll", None),
            "tour.collections.list_title",
            "tour.collections.list_body",
        ),
    ],
    "pdf": [
        TourStepDef(
            lambda h: getattr(h, "page_indicator", None),
            "tour.pdf.pages_title",
            "tour.pdf.pages_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "search_input", None),
            "tour.pdf.search_title",
            "tour.pdf.search_body",
        ),
        TourStepDef(
            _pdf_ocr_widget,
            "tour.pdf.ocr_title",
            "tour.pdf.ocr_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_highlight", None),
            "tour.pdf.highlight_title",
            "tour.pdf.highlight_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_sidebar", None)
            if getattr(h, "libro_id", None) and getattr(h, "_sidebar", None)
            else None,
            "tour.pdf.panel_title",
            "tour.pdf.panel_body",
        ),
        TourStepDef(
            lambda h: _pdf_tab_bar(h)
            if getattr(h, "libro_id", None) and getattr(h, "_sidebar", None)
            else None,
            "tour.pdf.annotations_title",
            "tour.pdf.annotations_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_reading", None),
            "tour.pdf.reading_title",
            "tour.pdf.reading_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_btn_fullscreen", None),
            "tour.pdf.fullscreen_title",
            "tour.pdf.fullscreen_body",
        ),
    ],
    "book_add": [
        TourStepDef(
            lambda h: getattr(h, "titulo_input", None),
            "tour.book.title_title",
            "tour.book.title_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "autor_input", None),
            "tour.book.author_title",
            "tour.book.author_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "genero_input", None),
            "tour.book.genre_title",
            "tour.book.genre_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_rating_picker", None),
            "tour.book.rating_title",
            "tour.book.rating_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_tags_section", None),
            "tour.book.tags_title",
            "tour.book.tags_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "boton_guardar", None),
            "tour.book.save_title",
            "tour.book.save_body",
        ),
    ],
    "book_edit": [
        TourStepDef(
            lambda h: getattr(h, "titulo_input", None),
            "tour.book.title_title",
            "tour.book.title_body",
        ),
        TourStepDef(
            _book_edit_file_or_author,
            "tour.book.replace_title",
            "tour.book.replace_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "genero_input", None),
            "tour.book.genre_title",
            "tour.book.genre_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_rating_picker", None),
            "tour.book.rating_title",
            "tour.book.rating_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "_tags_section", None),
            "tour.book.tags_title",
            "tour.book.tags_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "btn_eliminar", None),
            "tour.book.delete_title",
            "tour.book.delete_body",
        ),
        TourStepDef(
            lambda h: getattr(h, "boton_guardar", None),
            "tour.book.save_title",
            "tour.book.save_body",
        ),
    ],
    "collection_create": _collection_form_steps(),
    "collection_edit": _collection_form_steps(),
    "settings": _settings_form_steps(),
}

FULL_TOUR_SECTIONS = ("navigation", "library", "stats", "collections")


class _TourRepositionFilter(QObject):
    """Reposiciona el callout al redimensionar la ventana."""

    def __init__(self, tour: "SectionTour"):
        super().__init__()
        self._tour = tour

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Resize, QEvent.Move):
            QTimer.singleShot(0, self._tour._reposition_callout)
        return False


class TourCallout(QFrame):
    """Burbuja flotante con titulo, texto y navegacion del tour."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tourCallout")
        self.setStyleSheet(tour_callout_stylesheet())

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMaximumWidth(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        self._progress = QProgressBar()
        self._progress.setObjectName("tourProgress")
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)

        self._step_lbl = QLabel()
        self._step_lbl.setObjectName("tourStepIndicator")
        self._title = QLabel()
        self._title.setObjectName("tourTitle")
        self._title.setWordWrap(True)
        self._body = QLabel()
        self._body.setObjectName("tourBody")
        self._body.setWordWrap(True)

        root.addWidget(self._progress)
        root.addWidget(self._step_lbl)
        root.addWidget(self._title)
        root.addWidget(self._body)

        footer = QHBoxLayout()
        self._btn_skip = QPushButton()
        self._btn_skip.setObjectName("ghostButton")
        footer.addWidget(self._btn_skip)
        footer.addStretch()
        self._btn_back = QPushButton()
        self._btn_back.setObjectName("secondaryButton")
        self._btn_next = QPushButton()
        self._btn_next.setObjectName("primaryButton")
        footer.addWidget(self._btn_back)
        footer.addWidget(self._btn_next)
        root.addLayout(footer)

        wire_dialog_buttons(self._btn_back, self._btn_next)
        disable_button_default(self._btn_skip)

    def set_content(self, step_index: int, total: int, title_key: str, body_key: str):
        self._progress.setMaximum(max(total - 1, 0))
        self._progress.setValue(step_index)
        self._step_lbl.setText(tr("tour.step_indicator", current=step_index + 1, total=total))
        self._title.setText(tr(title_key))
        self._body.setText(tr(body_key))
        self._btn_skip.setText(tr("tour.skip"))
        self._btn_back.setText(tr("tour.back"))
        if step_index >= total - 1:
            self._btn_next.setText(tr("tour.finish"))
        else:
            self._btn_next.setText(tr("tour.next"))


class SectionTour:
    """Recorre los pasos de una seccion sobre widgets reales."""

    def __init__(
        self,
        host: QWidget,
        section: str,
        steps: List[TourStepDef],
        *,
        force: bool = False,
        on_chain: Optional[Callable[[], None]] = None,
    ):
        self.host = host
        self.section = section
        self.steps = steps
        self.force = force
        self.on_chain = on_chain
        self._index = 0
        self._highlighted: Optional[QWidget] = None
        self._callout = TourCallout(self.host)
        self._filter: Optional[_TourRepositionFilter] = None
        self._section_marked = False
        self._callout._btn_next.clicked.connect(self._next)
        self._callout._btn_back.clicked.connect(self._back)
        self._callout._btn_skip.clicked.connect(self._skip)

    def start(self):
        global _active_tour
        if not self.force:
            if not get_help_tips_enabled():
                self._chain_next()
                return
            if is_tour_section_seen(self.section):
                self._chain_next()
                return
        if _active_tour is not None:
            _active_tour._finish(mark_seen=False)
        _active_tour = self
        self._filter = _TourRepositionFilter(self)
        self.host.installEventFilter(self._filter)
        window = self.host.window()
        if window is not None and window is not self.host:
            window.installEventFilter(self._filter)
        self._show_step(0)

    def _clear_highlight(self):
        if self._highlighted is not None:
            self._highlighted.setProperty("tourHighlight", False)
            self._highlighted.style().unpolish(self._highlighted)
            self._highlighted.style().polish(self._highlighted)
            self._highlighted = None

    def _finish(self, mark_seen: bool = True):
        global _active_tour
        self._clear_highlight()
        self._callout.hide()
        if self._filter is not None:
            self.host.removeEventFilter(self._filter)
            window = self.host.window()
            if window is not None and window is not self.host:
                window.removeEventFilter(self._filter)
            self._filter = None
        if mark_seen:
            mark_tour_section_seen(self.section)
        _active_tour = None
        self._chain_next()

    def _chain_next(self):
        if self.on_chain:
            QTimer.singleShot(200, self.on_chain)

    def _skip(self):
        self._finish(mark_seen=True)

    def _back(self):
        if self._index > 0:
            self._show_step(self._index - 1)

    def _next(self):
        if self._index < len(self.steps) - 1:
            self._show_step(self._index + 1)
        else:
            self._finish(mark_seen=True)

    def _show_step(self, index: int):
        if index >= len(self.steps):
            self._finish(mark_seen=True)
            return
        step = self.steps[index]
        if step.prepare:
            step.prepare(self.host)
        self._index = index
        widget = step.resolve_widget(self.host)
        if widget is None or not widget.isVisible():
            if index < len(self.steps) - 1:
                self._show_step(index + 1)
            else:
                self._finish(mark_seen=True)
            return
        self._clear_highlight()
        self._highlighted = widget
        widget.setProperty("tourHighlight", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        self._callout.set_content(index, len(self.steps), step.title_key, step.body_key)
        self._callout._btn_back.setVisible(index > 0)
        self._callout.adjustSize()
        self._reposition_callout()
        self._callout.show()
        self._callout.raise_()
        if not self._section_marked:
            mark_tour_section_seen(self.section)
            self._section_marked = True

    def _reposition_callout(self):
        widget = self._highlighted
        if widget is None:
            return
        host = self.host
        widget_rect = widget.rect()
        top_left = host.mapFromGlobal(widget.mapToGlobal(widget_rect.topLeft()))
        bottom_left = host.mapFromGlobal(widget.mapToGlobal(widget_rect.bottomLeft()))
        callout_w = self._callout.width()
        callout_h = self._callout.height()
        host_w = host.width()
        host_h = host.height()

        x = top_left.x() + max(0, (widget_rect.width() - callout_w) // 2)
        y = bottom_left.y() + 10
        if y + callout_h > host_h - 8:
            y = top_left.y() - callout_h - 10
        x = max(8, min(x, host_w - callout_w - 8))
        y = max(8, min(y, host_h - callout_h - 8))
        self._callout.move(x, y)
        self._callout.raise_()


def dismiss_active_tour(host: Optional[QWidget] = None, *, mark_seen: bool = False) -> None:
    """Cierra el tour activo (p. ej. al cerrar un dialogo)."""
    global _active_tour
    if _active_tour is None:
        return
    if host is not None and _active_tour.host is not host:
        return
    _active_tour._finish(mark_seen=mark_seen)



def schedule_section_tour(
    host: QWidget,
    section: str,
    delay_ms: int = 450,
    *,
    retries: int = 8,
) -> None:
    """Programa el tour de una seccion si aun no se ha visto."""
    if section not in SECTION_STEPS:
        return
    if not get_help_tips_enabled():
        return
    if is_tour_section_seen(section):
        return

    def _run(attempt: int = 0):
        if _active_tour is not None:
            if attempt < retries:
                QTimer.singleShot(800, lambda a=attempt + 1: _run(a))
            return
        SectionTour(host, section, SECTION_STEPS[section]).start()

    QTimer.singleShot(delay_ms, _run)


def start_section_tour(host: QWidget, section: str, *, force: bool = True) -> None:
    """Inicia el tour de una seccion forzado (p. ej. desde Ajustes)."""
    global _active_tour
    if section not in SECTION_STEPS:
        return
    if _active_tour is not None:
        _active_tour._finish(mark_seen=False)
    SectionTour(host, section, SECTION_STEPS[section], force=force).start()


def start_full_tour(host: QWidget) -> None:
    """Recorre las secciones principales en secuencia."""
    sections = list(FULL_TOUR_SECTIONS)

    def _run_next():
        if not sections:
            return
        section = sections.pop(0)

        def _on_done():
            if sections:
                _run_next()

        SectionTour(
            host,
            section,
            SECTION_STEPS[section],
            force=True,
            on_chain=_on_done if sections else None,
        ).start()

    _run_next()
