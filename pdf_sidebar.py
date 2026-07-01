"""Panel lateral de anotaciones del visor PDF."""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from crud import (
    obtener_marcadores_por_libro, crear_marcador, eliminar_marcador,
    obtener_notas_por_libro, eliminar_nota,
    obtener_resaltados_por_libro, eliminar_resaltado,
    obtener_libro_por_id,
)
from i18n import tr
from notes_export import exportar_anotaciones


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

        self._bookmarks_list = QListWidget()
        self._bookmarks_list.setObjectName("viewerList")
        self._bookmarks_list.itemDoubleClicked.connect(self._goto_bookmark)
        self._tab_bookmarks = QWidget()
        bl = QVBoxLayout(self._tab_bookmarks)
        bl.setContentsMargins(0, 8, 0, 0)
        bl.addWidget(self._bookmarks_list)
        bb = QHBoxLayout()
        self._btn_add_bm = QPushButton()
        self._btn_add_bm.setObjectName("secondaryButton")
        self._btn_add_bm.clicked.connect(self._add_bookmark)
        self._btn_del_bm = QPushButton()
        self._btn_del_bm.setObjectName("ghostButton")
        self._btn_del_bm.clicked.connect(self._del_bookmark)
        bb.addWidget(self._btn_add_bm)
        bb.addWidget(self._btn_del_bm)
        bl.addLayout(bb)

        self._notes_list = QListWidget()
        self._notes_list.setObjectName("viewerList")
        self._notes_list.itemDoubleClicked.connect(self._goto_note)
        self._tab_notes = QWidget()
        nl = QVBoxLayout(self._tab_notes)
        nl.setContentsMargins(0, 8, 0, 0)
        nl.addWidget(self._notes_list)
        nb = QHBoxLayout()
        self._btn_add_note = QPushButton()
        self._btn_add_note.setObjectName("secondaryButton")
        self._btn_add_note.clicked.connect(self.add_note_requested.emit)
        self._btn_del_note = QPushButton()
        self._btn_del_note.setObjectName("ghostButton")
        self._btn_del_note.clicked.connect(self._del_note)
        nb.addWidget(self._btn_add_note)
        nb.addWidget(self._btn_del_note)
        nl.addLayout(nb)

        self._highlights_list = QListWidget()
        self._highlights_list.setObjectName("viewerList")
        self._highlights_list.itemDoubleClicked.connect(self._goto_highlight)
        self._tab_highlights = QWidget()
        hl = QVBoxLayout(self._tab_highlights)
        hl.setContentsMargins(0, 8, 0, 0)
        hl.addWidget(self._highlights_list)
        hb = QHBoxLayout()
        self._btn_del_hl = QPushButton()
        self._btn_del_hl.setObjectName("ghostButton")
        self._btn_del_hl.clicked.connect(self._del_highlight)
        hb.addStretch()
        hb.addWidget(self._btn_del_hl)
        hl.addLayout(hb)

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
            QMessageBox.information(
                self, tr("common.success"), tr("export.done", path=path_md)
            )
        else:
            QMessageBox.warning(self, tr("common.error"), tr("export.failed"))

    def reload(self):
        if not self.libro_id:
            return
        self._load_bookmarks()
        self._load_notes()
        self._load_highlights()

    def _load_bookmarks(self):
        self._bookmarks_list.clear()
        for m in obtener_marcadores_por_libro(self.libro_id):
            if m.etiqueta:
                label = tr("pdf.bookmark_item", name=m.etiqueta, page=m.pagina + 1)
            else:
                label = tr("pdf.bookmark_page_only", page=m.pagina + 1)
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, m.pagina)
            item.setData(Qt.UserRole + 1, m.id_marcador)
            self._bookmarks_list.addItem(item)

    def _load_notes(self):
        self._notes_list.clear()
        for n in obtener_notas_por_libro(self.libro_id):
            prefix = ""
            if n.pagina is not None:
                prefix = tr("pdf.note_page_prefix", page=n.pagina + 1)
            item = QListWidgetItem(f"{prefix}{n.titulo}")
            item.setData(Qt.UserRole, n.pagina if n.pagina is not None else 0)
            item.setData(Qt.UserRole + 1, n.id_nota)
            self._notes_list.addItem(item)

    def _load_highlights(self):
        self._highlights_list.clear()
        for h in obtener_resaltados_por_libro(self.libro_id):
            preview = (h.texto or "")[:60]
            if len(h.texto or "") > 60:
                preview += "…"
            item = QListWidgetItem(
                tr("pdf.highlight_item", page=h.pagina + 1, text=preview)
            )
            item.setData(Qt.UserRole, h.pagina)
            item.setData(Qt.UserRole + 1, h.id_resaltado)
            self._highlights_list.addItem(item)

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
