"""Diálogos modales de LiBooks."""

import logging

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QListWidget, QListWidgetItem, QComboBox, QMessageBox,
    QScrollArea, QWidget,
)
from PyQt5.QtCore import Qt

from crud import (
    crear_coleccion, agregar_libro_a_coleccion, obtener_libros, session,
)
from models import Coleccion
from icons import app_icon, icon_label, set_button_icon
from i18n import tr
from styles import ACCENT_TEXT, TEXT_PRIMARY, TEXT_SECONDARY

logger = logging.getLogger(__name__)


class ColeccionDialog(QDialog):
    """Modal para crear una nueva colección."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(520, 520)
        self.setModal(True)

        self._libros = obtener_libros()
        self._seleccionados = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        icon_box = QFrame()
        icon_box.setObjectName("dialogIconBox")
        il = QHBoxLayout(icon_box)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(icon_label("collection", 22))
        self._title = QLabel()
        self._title.setObjectName("dialogTitle")
        self._btn_close = QPushButton()
        self._btn_close.setObjectName("closeDialogBtn")
        self._btn_close.clicked.connect(self.reject)
        header.addWidget(icon_box)
        header.addWidget(self._title, 1)
        header.addWidget(self._btn_close)
        root.addLayout(header)

        self._lbl_titulo = QLabel()
        self._lbl_titulo.setObjectName("fieldLabel")
        self.titulo_input = QLineEdit()
        root.addWidget(self._lbl_titulo)
        root.addWidget(self.titulo_input)

        self._lbl_buscar = QLabel()
        self._lbl_buscar.setObjectName("fieldLabel")
        self.buscar_input = QLineEdit()
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

        footer = QHBoxLayout()
        footer.addStretch()
        self._btn_cancelar = QPushButton()
        self._btn_cancelar.setObjectName("secondaryButton")
        self._btn_cancelar.clicked.connect(self.reject)
        self._btn_crear = QPushButton()
        self._btn_crear.setObjectName("primaryButton")
        self._btn_crear.clicked.connect(self._crear)
        footer.addWidget(self._btn_cancelar)
        footer.addWidget(self._btn_crear)
        root.addLayout(footer)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("collection.create_title"))
        self._title.setText(tr("collection.create_title"))
        self._btn_close.setToolTip(tr("common.close"))
        set_button_icon(self._btn_close, "close", 16, TEXT_SECONDARY)
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
            self._btn_crear, "check", 16, ACCENT_TEXT, tr("collection.create_btn")
        )

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

    def _crear(self):
        titulo = self.titulo_input.text().strip()
        if not titulo:
            QMessageBox.warning(
                self, tr("common.error"), tr("collection.title_required")
            )
            return

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

        if not libros_ids:
            QMessageBox.warning(
                self, tr("common.error"), tr("collection.book_required")
            )
            return

        try:
            if not crear_coleccion(titulo):
                QMessageBox.warning(
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
            QMessageBox.information(
                self,
                tr("common.success"),
                tr("collection.created", title=titulo, count=len(libros_ids)),
            )
        except Exception as e:
            session.rollback()
            logger.exception("Error al crear colección: %s", e)
            QMessageBox.critical(
                self, tr("common.error"), tr("collection.create_error", error=e)
            )
