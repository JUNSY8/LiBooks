"""Panel lateral de anotaciones del visor PDF."""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFileDialog, QStackedWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from crud import (
    obtener_marcadores_por_libro, crear_marcador, eliminar_marcador,
    obtener_notas_por_libro, eliminar_nota,
    obtener_resaltados_por_libro, eliminar_resaltado,
    obtener_libro_por_id,
)
from i18n import tr
from message_boxes import show_info, show_warning
from notes_export import exportar_anotaciones


def _clip_text(text: str, max_len: int = 88) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class _AnnotationCard(QFrame):
    """Tarjeta clickeable para un ítem del panel de anotaciones."""

    activated = pyqtSignal()

    def __init__(self, accent_object_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("annotationCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("selected", False)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 10, 0)
        root.setSpacing(10)

        self._accent = QFrame()
        self._accent.setObjectName(accent_object_name)
        self._accent.setFixedWidth(4)

        body = QVBoxLayout()
        body.setContentsMargins(0, 10, 0, 10)
        body.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)
        self._page_badge = QLabel()
        self._page_badge.setObjectName("annotationPageBadge")
        header.addWidget(self._page_badge, 0, Qt.AlignLeft)
        header.addStretch()
        self._kind_label = QLabel()
        self._kind_label.setObjectName("annotationKindLabel")
        header.addWidget(self._kind_label, 0, Qt.AlignRight)

        self._title = QLabel()
        self._title.setObjectName("annotationTitle")
        self._title.setWordWrap(True)

        self._preview = QLabel()
        self._preview.setObjectName("annotationPreview")
        self._preview.setWordWrap(True)
        self._preview.hide()

        body.addLayout(header)
        body.addWidget(self._title)
        body.addWidget(self._preview)

        root.addWidget(self._accent)
        root.addLayout(body, 1)

    def set_content(
        self,
        page_label: str,
        title: str,
        preview: str = "",
        kind_label: str = "",
    ) -> None:
        self._page_badge.setText(page_label)
        if title:
            self._title.setText(title)
            self._title.show()
        else:
            self._title.clear()
            self._title.hide()
        if preview:
            self._preview.setText(preview)
            self._preview.show()
        else:
            self._preview.clear()
            self._preview.hide()
        if kind_label:
            self._kind_label.setText(kind_label)
            self._kind_label.show()
        else:
            self._kind_label.clear()
            self._kind_label.hide()

    def set_preview_emphasis(self, emphasized: bool = False) -> None:
        self._preview.setObjectName(
            "annotationHighlightQuote" if emphasized else "annotationPreview"
        )

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.activated.emit()
        super().mouseDoubleClickEvent(event)


class AnnotationsPanel(QFrame):
    """Marcadores, notas y resaltados del libro actual."""

    goto_page = pyqtSignal(int)
    add_note_requested = pyqtSignal()
    refresh_highlights = pyqtSignal()

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.libro_id = viewer.libro_id
        self.setObjectName("viewerSidebar")
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel()
        title.setObjectName("viewerSidebarTitle")
        self._title = title
        root.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("viewerTabs")

        self._bookmarks_list, self._bookmarks_empty, self._tab_bookmarks = (
            self._build_annotation_tab("bookmark")
        )
        self._bookmarks_list.itemDoubleClicked.connect(self._goto_bookmark)
        self._bookmarks_list.itemSelectionChanged.connect(
            lambda: self._sync_card_selection(self._bookmarks_list)
        )

        self._notes_list, self._notes_empty, self._tab_notes = (
            self._build_annotation_tab("note", add_note=True)
        )
        self._notes_list.itemDoubleClicked.connect(self._goto_note)
        self._notes_list.itemSelectionChanged.connect(
            lambda: self._sync_card_selection(self._notes_list)
        )

        self._highlights_list, self._highlights_empty, self._tab_highlights = (
            self._build_annotation_tab("highlight", delete_only=True)
        )
        self._highlights_list.itemDoubleClicked.connect(self._goto_highlight)
        self._highlights_list.itemSelectionChanged.connect(
            lambda: self._sync_card_selection(self._highlights_list)
        )

        self.tabs.addTab(self._tab_bookmarks, "")
        self.tabs.addTab(self._tab_notes, "")
        self.tabs.addTab(self._tab_highlights, "")
        root.addWidget(self.tabs, 1)

        self._btn_export = QPushButton()
        self._btn_export.setObjectName("secondaryButton")
        self._btn_export.clicked.connect(self._export_annotations)
        root.addWidget(self._btn_export)

        self.retranslate_ui()
        self.reload()

    def _build_annotation_tab(self, kind: str, add_note: bool = False, delete_only: bool = False):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        stack = QStackedWidget()
        list_widget = QListWidget()
        list_widget.setObjectName("viewerList")
        list_widget.setSpacing(6)
        list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        empty = QLabel()
        empty.setObjectName("annotationEmpty")
        empty.setAlignment(Qt.AlignCenter)
        empty.setWordWrap(True)
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        stack.addWidget(list_widget)
        stack.addWidget(empty)
        layout.addWidget(stack, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        if kind == "bookmark":
            self._btn_add_bm = QPushButton()
            self._btn_add_bm.setObjectName("secondaryButton")
            self._btn_add_bm.clicked.connect(self._add_bookmark)
            self._btn_del_bm = QPushButton()
            self._btn_del_bm.setObjectName("ghostButton")
            self._btn_del_bm.clicked.connect(self._del_bookmark)
            buttons.addWidget(self._btn_add_bm)
            buttons.addWidget(self._btn_del_bm)
        elif add_note:
            self._btn_add_note = QPushButton()
            self._btn_add_note.setObjectName("secondaryButton")
            self._btn_add_note.clicked.connect(self.add_note_requested.emit)
            self._btn_del_note = QPushButton()
            self._btn_del_note.setObjectName("ghostButton")
            self._btn_del_note.clicked.connect(self._del_note)
            buttons.addWidget(self._btn_add_note)
            buttons.addWidget(self._btn_del_note)
        elif delete_only:
            self._btn_del_hl = QPushButton()
            self._btn_del_hl.setObjectName("ghostButton")
            self._btn_del_hl.clicked.connect(self._del_highlight)
            buttons.addStretch()
            buttons.addWidget(self._btn_del_hl)

        layout.addLayout(buttons)

        list_widget._empty_stack = stack  # noqa: SLF001 — referencia interna al stack
        return list_widget, empty, tab

    def retranslate_ui(self):
        self._title.setText(tr("pdf.panel_title"))
        self.tabs.setTabText(0, tr("pdf.bookmarks"))
        self.tabs.setTabText(1, tr("pdf.notes"))
        self.tabs.setTabText(2, tr("pdf.highlights"))
        self._btn_add_bm.setText(tr("pdf.add_bookmark"))
        self._btn_del_bm.setText(tr("pdf.delete"))
        self._btn_add_note.setText(tr("pdf.new_note"))
        self._btn_del_note.setText(tr("pdf.delete"))
        self._btn_del_hl.setText(tr("pdf.delete"))
        self._btn_export.setText(tr("export.btn"))
        self._bookmarks_empty.setText(tr("pdf.no_bookmarks"))
        self._notes_empty.setText(tr("pdf.no_notes"))
        self._highlights_empty.setText(tr("pdf.no_highlights"))
        self.tabs.setTabToolTip(0, tr("pdf.bookmarks_tooltip"))
        self.tabs.setTabToolTip(1, tr("pdf.notes_tooltip"))
        self.tabs.setTabToolTip(2, tr("pdf.highlights_tooltip"))
        self._title.setToolTip(tr("pdf.panel_title_tooltip"))
        self._btn_add_bm.setToolTip(tr("pdf.add_bookmark_tooltip"))
        self._btn_add_note.setToolTip(tr("pdf.new_note_tooltip"))
        self._btn_export.setToolTip(tr("pdf.export_annotations_tooltip"))
        self.reload()

    def _page_label(self, page: int) -> str:
        return tr("pdf.page_badge", page=page + 1)

    def _add_card(
        self,
        list_widget: QListWidget,
        card: _AnnotationCard,
        pagina: int,
        entity_id: int,
        height: int,
    ) -> None:
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, height))
        item.setData(Qt.UserRole, pagina)
        item.setData(Qt.UserRole + 1, entity_id)
        list_widget.addItem(item)
        list_widget.setItemWidget(item, card)

    def _toggle_empty(self, list_widget: QListWidget, has_items: bool) -> None:
        stack = getattr(list_widget, "_empty_stack", None)
        if stack is not None:
            stack.setCurrentIndex(0 if has_items else 1)

    def _sync_card_selection(self, list_widget: QListWidget) -> None:
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            card = list_widget.itemWidget(item)
            if isinstance(card, _AnnotationCard):
                card.set_selected(item is list_widget.currentItem())

    def _export_annotations(self):
        if not self.libro_id:
            return
        libro = obtener_libro_por_id(self.libro_id)
        titulo = (libro.titulo if libro else None) or "libro"
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in titulo)[:40]
        path_md, _ = QFileDialog.getSaveFileName(
            self,
            tr("export.dialog_title"),
            f"{safe}_anotaciones.md",
            tr("export.filter_md"),
        )
        if not path_md:
            return
        fmt = "txt" if path_md.lower().endswith(".txt") else "md"
        if exportar_anotaciones(self.libro_id, path_md, formato=fmt):
            show_info(self, tr("common.success"), tr("export.done", path=path_md))
        else:
            show_warning(self, tr("common.error"), tr("export.failed"))

    def reload(self):
        if not self.libro_id:
            return
        self._load_bookmarks()
        self._load_notes()
        self._load_highlights()

    def _load_bookmarks(self):
        self._bookmarks_list.clear()
        marcadores = obtener_marcadores_por_libro(self.libro_id)
        for m in marcadores:
            title = m.etiqueta or tr("pdf.bookmark_untitled")
            card = _AnnotationCard("annotationAccentBookmark")
            card.set_content(
                self._page_label(m.pagina),
                title,
                kind_label=tr("pdf.bookmarks"),
            )
            card.activated.connect(
                lambda p=m.pagina: self.goto_page.emit(p)
            )
            self._add_card(
                self._bookmarks_list, card, m.pagina, m.id_marcador, 72
            )
        self._toggle_empty(self._bookmarks_list, bool(marcadores))

    def _load_notes(self):
        self._notes_list.clear()
        notas = obtener_notas_por_libro(self.libro_id)
        for n in notas:
            preview = _clip_text(n.fragmento or n.contenido or "")
            card = _AnnotationCard("annotationAccentNote")
            page = n.pagina if n.pagina is not None else 0
            card.set_content(
                self._page_label(page) if n.pagina is not None else tr("pdf.note_no_page"),
                n.titulo,
                preview=preview,
                kind_label=tr("pdf.notes"),
            )
            card.activated.connect(lambda p=page: self.goto_page.emit(p))
            self._add_card(self._notes_list, card, page, n.id_nota, 88 if preview else 72)
        self._toggle_empty(self._notes_list, bool(notas))

    def _load_highlights(self):
        self._highlights_list.clear()
        resaltados = obtener_resaltados_por_libro(self.libro_id)
        for h in resaltados:
            quote = _clip_text(h.texto or "", 96)
            card = _AnnotationCard("annotationAccentHighlight")
            card.set_content(
                self._page_label(h.pagina),
                "",
                preview=f"“{quote}”" if quote else tr("pdf.highlight_empty"),
                kind_label=tr("pdf.highlights"),
            )
            card.set_preview_emphasis(True)
            card.activated.connect(lambda p=h.pagina: self.goto_page.emit(p))
            self._add_card(
                self._highlights_list, card, h.pagina, h.id_resaltado, 80
            )
        self._toggle_empty(self._highlights_list, bool(resaltados))

    def _add_bookmark(self):
        if not self.libro_id:
            return
        pagina = self.viewer.current_page
        nombre = self.viewer.prompt_bookmark_name(pagina)
        if nombre is None:
            return
        etiqueta = nombre if nombre else None
        if crear_marcador(self.libro_id, pagina, etiqueta=etiqueta):
            self._load_bookmarks()

    def _del_bookmark(self):
        item = self._bookmarks_list.currentItem()
        if item and eliminar_marcador(item.data(Qt.UserRole + 1)):
            self._load_bookmarks()

    def _del_note(self):
        item = self._notes_list.currentItem()
        if item and eliminar_nota(item.data(Qt.UserRole + 1)):
            self._load_notes()

    def _del_highlight(self):
        item = self._highlights_list.currentItem()
        if item and eliminar_resaltado(item.data(Qt.UserRole + 1)):
            self._load_highlights()
            self.refresh_highlights.emit()

    def _goto_bookmark(self, item):
        self.goto_page.emit(item.data(Qt.UserRole))

    def _goto_note(self, item):
        self.goto_page.emit(item.data(Qt.UserRole))

    def _goto_highlight(self, item):
        self.goto_page.emit(item.data(Qt.UserRole))
