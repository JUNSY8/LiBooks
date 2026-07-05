"""Diálogos modales de LiBooks."""

import logging

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QListWidget, QListWidgetItem, QComboBox,
    QScrollArea, QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer

from crud import (
    crear_coleccion, agregar_libro_a_coleccion, actualizar_coleccion,
    obtener_coleccion_por_id, obtener_libros, session,
)
from models import Coleccion
from icons import set_button_icon
from i18n import tr
from message_boxes import wire_dialog_buttons, show_info, show_warning, show_error
from title_bar import FramelessDialog
from dialog_layout import (
    DIALOG_PAGE_MARGINS,
    attach_footer_bar,
    compact_button_row,
)
from styles import ACCENT_TEXT, TEXT_PRIMARY, TEXT_SECONDARY

logger = logging.getLogger(__name__)


class ColeccionDialog(FramelessDialog):
    """Modal para crear o editar una colección."""

    def __init__(self, parent=None, coleccion_id=None):
        super().__init__(parent)
        self.setMinimumSize(520, 520)
        self.setModal(True)

        self._coleccion_id = coleccion_id
        self._coleccion = (
            obtener_coleccion_por_id(coleccion_id) if coleccion_id else None
        )
        self._libros = obtener_libros()
        self._seleccionados = {}
        if self._coleccion:
            for libro in self._coleccion.libros:
                self._seleccionados[libro.id_libro] = libro.titulo

        self._init_frameless_dialog()
        outer = self.frameless_layout(margins=(0, 0, 0, 0), spacing=0)

        form = QWidget()
        root = QVBoxLayout(form)
        root.setContentsMargins(*DIALOG_PAGE_MARGINS)
        root.setSpacing(16)

        self._lbl_titulo = QLabel()
        self._lbl_titulo.setObjectName("fieldLabel")
        self.titulo_input = QLineEdit()
        self.titulo_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if self._coleccion:
            self.titulo_input.setText(self._coleccion.nombre)
        root.addWidget(self._lbl_titulo)
        root.addWidget(self.titulo_input)

        self._lbl_buscar = QLabel()
        self._lbl_buscar.setObjectName("fieldLabel")
        self.buscar_input = QLineEdit()
        self.buscar_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.buscar_input.textChanged.connect(self._filtrar_libros)
        root.addWidget(self._lbl_buscar)
        root.addWidget(self.buscar_input)

        self.libros_list = QListWidget()
        self.libros_list.setObjectName("dialogBookList")
        self.libros_list.setSelectionMode(QListWidget.MultiSelection)
        self.libros_list.setMinimumHeight(140)
        self._poblar_lista_libros()
        self.libros_list.itemSelectionChanged.connect(self._sync_tags)
        root.addWidget(self.libros_list)

        self._lbl_tags = QLabel()
        self._lbl_tags.setObjectName("fieldLabel")
        root.addWidget(self._lbl_tags)

        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setMaximumHeight(80)
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(8)
        self.tags_layout.addStretch()
        self.tags_scroll.setWidget(self.tags_container)
        root.addWidget(self.tags_scroll)

        filtros_row = QHBoxLayout()
        filtros_row.setSpacing(12)

        col_autor = QVBoxLayout()
        self._lbl_autor = QLabel()
        self._lbl_autor.setObjectName("fieldLabel")
        self.autor_combo = QComboBox()
        self.autor_combo.addItem("", None)
        autores = {}
        for libro in self._libros:
            if libro.autor and libro.autor.id_autor not in autores:
                autores[libro.autor.id_autor] = libro.autor
                self.autor_combo.addItem(libro.autor.nombre, libro.autor)
        col_autor.addWidget(self._lbl_autor)
        col_autor.addWidget(self.autor_combo)

        col_genero = QVBoxLayout()
        self._lbl_genero = QLabel()
        self._lbl_genero.setObjectName("fieldLabel")
        self.genero_combo = QComboBox()
        self.genero_combo.addItem("", None)
        generos = {}
        for libro in self._libros:
            if libro.genero and libro.genero.id_genero not in generos:
                generos[libro.genero.id_genero] = libro.genero
                self.genero_combo.addItem(libro.genero.nombre, libro.genero)
        col_genero.addWidget(self._lbl_genero)
        col_genero.addWidget(self.genero_combo)

        filtros_row.addLayout(col_autor, 1)
        filtros_row.addLayout(col_genero, 1)
        root.addLayout(filtros_row)

        divider = QFrame()
        divider.setObjectName("dialogDivider")
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(form)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        self._btn_cancelar = QPushButton()
        self._btn_cancelar.setObjectName("secondaryButton")
        self._btn_cancelar.clicked.connect(self.reject)
        self._btn_crear = QPushButton()
        self._btn_crear.setObjectName("primaryButton")
        self._btn_crear.clicked.connect(self._guardar)
        footer.addWidget(self._btn_cancelar)
        footer.addWidget(self._btn_crear)
        attach_footer_bar(outer, footer)

        wire_dialog_buttons(self._btn_cancelar, self._btn_crear)

        self.retranslate_ui()
        self._render_tags()
        QTimer.singleShot(450, self._schedule_tour)

    def _schedule_tour(self):
        from product_tour import schedule_section_tour
        section = "collection_edit" if self._coleccion_id else "collection_create"
        schedule_section_tour(self, section, delay_ms=50)

    def closeEvent(self, event):
        from product_tour import dismiss_active_tour
        dismiss_active_tour(self, mark_seen=True)
        super().closeEvent(event)

    def retranslate_ui(self):
        editing = self._coleccion_id is not None
        title_key = "collection.edit_title" if editing else "collection.create_title"
        btn_key = "collection.save_btn" if editing else "collection.create_btn"
        btn_icon = "edit" if editing else "add_collection"

        self.set_frameless_title(tr(title_key))
        self._lbl_titulo.setText(tr("collection.title_label"))
        self.titulo_input.setPlaceholderText(tr("collection.title_placeholder"))
        self._lbl_buscar.setText(tr("collection.search_label"))
        self.buscar_input.setPlaceholderText(tr("collection.search_placeholder"))
        self._lbl_tags.setText(tr("collection.selected_label"))
        self._lbl_autor.setText(tr("collection.filter_author"))
        self.autor_combo.setItemText(0, tr("collection.select_author"))
        self._lbl_genero.setText(tr("collection.filter_genre"))
        self.genero_combo.setItemText(0, tr("collection.select_genre"))
        self._btn_cancelar.setText(tr("common.cancel"))
        set_button_icon(
            self._btn_crear, btn_icon, 16, ACCENT_TEXT, tr(btn_key)
        )
        self._apply_tooltips()

    def _apply_tooltips(self):
        self.titulo_input.setToolTip(tr("collection.title_tooltip"))
        self.buscar_input.setToolTip(tr("collection.search_tooltip"))
        self.libros_list.setToolTip(tr("collection.books_list_tooltip"))
        self.autor_combo.setToolTip(tr("collection.filter_author_tooltip"))
        self.genero_combo.setToolTip(tr("collection.filter_genre_tooltip"))
        self._btn_crear.setToolTip(tr("collection.save_tooltip"))

    def _poblar_lista_libros(self, filtro=""):
        self.libros_list.clear()
        filtro = filtro.lower()
        for libro in self._libros:
            if filtro and filtro not in libro.titulo.lower():
                continue
            item = QListWidgetItem(libro.titulo)
            item.setData(Qt.UserRole, libro.id_libro)
            self.libros_list.addItem(item)
            if libro.id_libro in self._seleccionados:
                item.setSelected(True)

    def _filtrar_libros(self, texto):
        self._poblar_lista_libros(texto)

    def _sync_tags(self):
        for i in range(self.libros_list.count()):
            item = self.libros_list.item(i)
            lid = item.data(Qt.UserRole)
            if item.isSelected():
                self._seleccionados[lid] = item.text()
            elif lid in self._seleccionados:
                del self._seleccionados[lid]
        self._render_tags()

    def _render_tags(self):
        while self.tags_layout.count() > 1:
            w = self.tags_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        for lid, titulo in self._seleccionados.items():
            chip = QFrame()
            chip.setObjectName("tagChip")
            cl = QHBoxLayout(chip)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.setSpacing(4)
            lbl = QLabel(titulo)
            lbl.setObjectName("tagText")
            btn_x = QPushButton()
            btn_x.setObjectName("tagRemove")
            btn_x.setToolTip(tr("collection.remove_tag"))
            set_button_icon(btn_x, "close", 12, TEXT_PRIMARY)
            btn_x.clicked.connect(lambda _, id=lid: self._quitar_tag(id))
            cl.addWidget(lbl)
            cl.addWidget(btn_x)
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, chip)

    def _quitar_tag(self, libro_id):
        self._seleccionados.pop(libro_id, None)
        for i in range(self.libros_list.count()):
            item = self.libros_list.item(i)
            if item.data(Qt.UserRole) == libro_id:
                item.setSelected(False)
        self._render_tags()

    def _libros_seleccionados(self):
        libros_ids = list(self._seleccionados.keys())

        autor = self.autor_combo.currentData()
        genero = self.genero_combo.currentData()
        if autor or genero:
            for libro in self._libros:
                match = (
                    (autor and libro.autor and libro.autor.id_autor == autor.id_autor)
                    or (genero and libro.genero and libro.genero.id_genero == genero.id_genero)
                )
                if match and libro.id_libro not in libros_ids:
                    libros_ids.append(libro.id_libro)

        return libros_ids

    def _guardar(self):
        titulo = self.titulo_input.text().strip()
        if not titulo:
            show_warning(
                self, tr("common.error"), tr("collection.title_required")
            )
            return

        libros_ids = self._libros_seleccionados()
        if not libros_ids:
            show_warning(
                self, tr("common.error"), tr("collection.book_required")
            )
            return

        if self._coleccion_id:
            self._actualizar(titulo, libros_ids)
        else:
            self._crear(titulo, libros_ids)

    def _actualizar(self, titulo, libros_ids):
        try:
            if not actualizar_coleccion(self._coleccion_id, titulo, libros_ids):
                show_warning(
                    self, tr("common.error"), tr("collection.name_exists")
                )
                return

            self.accept()
            show_info(
                self,
                tr("common.success"),
                tr("collection.updated", title=titulo, count=len(libros_ids)),
            )
        except Exception as e:
            session.rollback()
            logger.exception("Error al actualizar colección: %s", e)
            show_error(
                self, tr("common.error"), tr("collection.update_error", error=e)
            )

    def _crear(self, titulo, libros_ids):
        try:
            if not crear_coleccion(titulo):
                show_warning(
                    self, tr("common.error"), tr("collection.name_exists")
                )
                return

            coleccion = session.query(Coleccion).filter_by(nombre=titulo).first()
            if not coleccion:
                raise RuntimeError("Collection not found after creation")

            for libro_id in libros_ids:
                agregar_libro_a_coleccion(coleccion.id_coleccion, libro_id)

            session.commit()
            self.accept()
            show_info(
                self,
                tr("common.success"),
                tr("collection.created", title=titulo, count=len(libros_ids)),
            )
        except Exception as e:
            session.rollback()
            logger.exception("Error al crear colección: %s", e)
            show_error(
                self, tr("common.error"), tr("collection.create_error", error=e)
            )
