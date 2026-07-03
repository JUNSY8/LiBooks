"""Diálogo modal para añadir o editar un libro."""

import os
from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGridLayout, QFileDialog, QSizePolicy, QComboBox,
    QScrollArea, QWidget,
)
from PyQt5.QtCore import Qt

from icons import app_icon, icon_label, set_button_icon
from i18n import tr
from message_boxes import wire_dialog_buttons, disable_button_default
from reading_status import (
    obtener_estado_efectivo,
    etiquetas_personalizadas_libro,
    etiqueta_de_estado,
    es_etiqueta_de_estado,
    etiquetas_opciones_estado,
    resolver_estado_desde_etiqueta,
    construir_etiquetas_guardado,
    separar_etiquetas_y_estado,
)
from brillo_picker import BrilloPicker
from crud import obtener_brillo_libro
from tag_picker import TAG_STATUS_CHIP_NAMES
from styles import ACCENT_TEXT, TEXT_PRIMARY, TEXT_SECONDARY


class Datos(QDialog):
    """Formulario modal de libro (añadir / editar)."""

    def __init__(self, parent=None, modo="añadir", archivo=None, libro_id=None):
        super().__init__(parent)
        self.modo = modo
        self.archivo = archivo
        self.libro_id = libro_id
        self._archivo_reemplazo = None

        self.setWindowIcon(app_icon())
        self.setMinimumWidth(480)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)
        self._tags: List[str] = []
        self._estado_manual: Optional[str] = None
        self._estado_efectivo: str = "unread"

        header = QHBoxLayout()
        icon_box = QFrame()
        icon_box.setObjectName("dialogIconBox")
        icon_layout = QHBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        header_icon = "edit" if modo == "editar" else "book"
        icon_layout.addWidget(icon_label(header_icon, 22))

        self._title = QLabel()
        self._title.setObjectName("dialogTitle")

        self._btn_close = QPushButton()
        self._btn_close.setObjectName("closeDialogBtn")
        self._btn_close.clicked.connect(self.reject)

        header.addWidget(icon_box)
        header.addWidget(self._title, 1)
        header.addWidget(self._btn_close)
        root.addLayout(header)

        self.file_section = QFrame()
        self.file_section.setObjectName("fileInfoBox")
        file_layout = QHBoxLayout(self.file_section)
        file_layout.setContentsMargins(16, 12, 16, 12)
        file_layout.setSpacing(12)

        file_icon_box = QFrame()
        file_icon_box.setObjectName("bookIconBox")
        fi_layout = QHBoxLayout(file_icon_box)
        fi_layout.setContentsMargins(0, 0, 0, 0)
        fi_layout.addWidget(icon_label("book", 28))

        file_text_layout = QVBoxLayout()
        file_text_layout.setSpacing(2)
        self._lbl_archivo = QLabel()
        self._lbl_archivo.setObjectName("fieldLabel")
        self.lbl_nombre_archivo = QLabel("")
        self.lbl_nombre_archivo.setStyleSheet("background: transparent; font-size: 13px;")
        self.lbl_nombre_archivo.setWordWrap(True)
        file_text_layout.addWidget(self._lbl_archivo)
        file_text_layout.addWidget(self.lbl_nombre_archivo)

        self._btn_reemplazar = QPushButton()
        self._btn_reemplazar.setObjectName("secondaryButton")
        self._btn_reemplazar.clicked.connect(self._reemplazar_archivo)

        file_layout.addWidget(file_icon_box)
        file_layout.addLayout(file_text_layout, 1)
        file_layout.addWidget(self._btn_reemplazar)
        root.addWidget(self.file_section)

        if archivo:
            self.lbl_nombre_archivo.setText(os.path.basename(archivo))
        elif modo == "añadir":
            self.file_section.hide()

        self._lbl_titulo = QLabel()
        self._lbl_titulo.setObjectName("fieldLabel")
        self.titulo_input = QLineEdit()
        self.titulo_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_autor_genero = QGridLayout()
        row_autor_genero.setHorizontalSpacing(16)
        row_autor_genero.setVerticalSpacing(8)
        self._lbl_autor = QLabel()
        self._lbl_autor.setObjectName("fieldLabel")
        self.autor_input = QLineEdit()
        self._lbl_genero = QLabel()
        self._lbl_genero.setObjectName("fieldLabel")
        self.genero_input = QLineEdit()

        row_autor_genero.addWidget(self._lbl_autor, 0, 0)
        row_autor_genero.addWidget(self._lbl_genero, 0, 1)
        row_autor_genero.addWidget(self.autor_input, 1, 0)
        row_autor_genero.addWidget(self.genero_input, 1, 1)

        root.addWidget(self._lbl_titulo)
        root.addWidget(self.titulo_input)
        root.addLayout(row_autor_genero)

        self._brillo_section = QFrame()
        brillo_layout = QVBoxLayout(self._brillo_section)
        brillo_layout.setContentsMargins(0, 4, 0, 0)
        brillo_layout.setSpacing(6)
        self._lbl_brillo = QLabel()
        self._lbl_brillo.setObjectName("fieldLabel")
        self._lbl_brillo_hint = QLabel()
        self._lbl_brillo_hint.setObjectName("fieldHint")
        brillo_layout.addWidget(self._lbl_brillo)
        brillo_layout.addWidget(self._lbl_brillo_hint)
        self._brillo_picker = BrilloPicker()
        brillo_layout.addWidget(self._brillo_picker)
        root.addWidget(self._brillo_section)

        self._tags_section = QFrame()
        self._tags_section.setObjectName("tagsSection")
        tags_section_layout = QVBoxLayout(self._tags_section)
        tags_section_layout.setContentsMargins(0, 4, 0, 0)
        tags_section_layout.setSpacing(10)

        self._lbl_etiquetas = QLabel()
        self._lbl_etiquetas.setObjectName("fieldLabel")
        self._lbl_tags_hint = QLabel()
        self._lbl_tags_hint.setObjectName("fieldHint")
        tags_section_layout.addWidget(self._lbl_etiquetas)
        tags_section_layout.addWidget(self._lbl_tags_hint)

        self._tags_scroll = QScrollArea()
        self._tags_scroll.setObjectName("tagsBadgeScroll")
        self._tags_scroll.setWidgetResizable(True)
        self._tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tags_scroll.setMinimumHeight(56)
        self._tags_scroll.setMaximumHeight(112)

        self._tags_container = QWidget()
        self._tags_layout = QHBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(10, 10, 10, 10)
        self._tags_layout.setSpacing(8)
        self._tags_layout.addStretch()
        self._tags_scroll.setWidget(self._tags_container)
        tags_section_layout.addWidget(self._tags_scroll)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(10)
        self._tag_picker = QComboBox()
        self._tag_picker.setEditable(True)
        self._tag_picker.setInsertPolicy(QComboBox.NoInsert)
        self._tag_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._tag_picker.lineEdit().returnPressed.connect(self._append_tag_from_picker)
        self._btn_add_tag = QPushButton()
        self._btn_add_tag.setObjectName("secondaryButton")
        self._btn_add_tag.clicked.connect(self._append_tag_from_picker)
        tag_row.addWidget(self._tag_picker, 1)
        tag_row.addWidget(self._btn_add_tag)
        tags_section_layout.addLayout(tag_row)
        root.addWidget(self._tags_section)

        divider = QFrame()
        divider.setObjectName("dialogDivider")
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        footer = QHBoxLayout()
        footer.setSpacing(10)

        self.btn_eliminar = QPushButton()
        self.btn_eliminar.setObjectName("dangerButton")
        self.btn_eliminar.hide()

        self._btn_cancelar = QPushButton()
        self._btn_cancelar.setObjectName("secondaryButton")
        self._btn_cancelar.clicked.connect(self.reject)

        self.boton_guardar = QPushButton()
        self.boton_guardar.setObjectName("primaryButton")
        self.boton_guardar.clicked.connect(self.accept)

        footer.addWidget(self.btn_eliminar)
        footer.addStretch()
        footer.addWidget(self._btn_cancelar)
        footer.addWidget(self.boton_guardar)
        root.addLayout(footer)

        wire_dialog_buttons(self._btn_cancelar, self.boton_guardar)
        disable_button_default(self._btn_close)
        disable_button_default(self.btn_eliminar)

        self.retranslate_ui()
        self._refresh_tag_suggestions()

    def retranslate_ui(self):
        title_key = (
            "book_dialog.edit_title" if self.modo == "editar" else "book_dialog.add_title"
        )
        self.setWindowTitle(tr(title_key))
        self._title.setText(tr(title_key))
        self._btn_close.setToolTip(tr("book_dialog.close"))
        set_button_icon(self._btn_close, "close", 16, TEXT_SECONDARY)
        self._lbl_archivo.setText(tr("book_dialog.current_file"))
        set_button_icon(
            self._btn_reemplazar, "replace", 16, None, tr("book_dialog.replace_file")
        )
        self._lbl_titulo.setText(tr("book_dialog.field_title"))
        self.titulo_input.setPlaceholderText(tr("book_dialog.title_placeholder"))
        self._lbl_autor.setText(tr("book_dialog.field_author"))
        self.autor_input.setPlaceholderText(tr("book_dialog.author_placeholder"))
        self._lbl_genero.setText(tr("book_dialog.field_genre"))
        self.genero_input.setPlaceholderText(tr("book_dialog.genre_placeholder"))
        self._lbl_brillo.setText(tr("book_dialog.field_brillo"))
        self._lbl_brillo_hint.setText(tr("book_dialog.brillo_hint"))
        self._brillo_picker.retranslate_ui()
        self._lbl_etiquetas.setText(tr("book_dialog.field_tags"))
        self._lbl_tags_hint.setText(tr("book_dialog.tags_hint"))
        self._btn_add_tag.setText(tr("book_dialog.add_tag_btn"))
        self._tag_picker.lineEdit().setPlaceholderText(tr("book_dialog.tag_picker_placeholder"))
        set_button_icon(
            self.btn_eliminar, "trash", 16, None, tr("book_dialog.delete")
        )
        self._btn_cancelar.setText(tr("common.cancel"))
        save_key = (
            "book_dialog.save" if self.modo == "editar" else "book_dialog.add_btn"
        )
        set_button_icon(
            self.boton_guardar, "check", 16, ACCENT_TEXT, tr(save_key)
        )
        self._refresh_tag_suggestions()

    def set_brillo_libro(self, libro):
        self._brillo_picker.set_nivel(obtener_brillo_libro(libro))

    def obtener_brillo(self) -> int:
        return self._brillo_picker.nivel()

    def set_etiquetas_libro(self, libro):
        """Carga estado y etiquetas libres desde un libro."""
        self._estado_manual = getattr(libro, "estado_manual", None)
        self._estado_efectivo = obtener_estado_efectivo(libro)
        self._tags = etiquetas_personalizadas_libro(libro)
        self._render_tag_badges()
        self._refresh_tag_suggestions()

    def set_etiquetas(self, nombres: List[str]):
        """Carga etiquetas (incl. estados) como badges."""
        estado, otras = separar_etiquetas_y_estado(nombres)
        if estado:
            self._estado_manual = estado
        self._tags = otras
        self._render_tag_badges()
        self._refresh_tag_suggestions()

    def obtener_etiquetas(self) -> List[str]:
        return construir_etiquetas_guardado(self._estado_manual, self._tags)

    def obtener_estado_manual(self) -> str:
        return self._estado_manual or "auto"

    def _estado_visible(self) -> str:
        return self._estado_manual or self._estado_efectivo

    def _picker_tag_names(self) -> List[str]:
        from crud import obtener_etiquetas

        nombres = [tr("reading_status.auto"), *etiquetas_opciones_estado()]
        for e in obtener_etiquetas():
            if not es_etiqueta_de_estado(e.nombre):
                nombres.append(e.nombre)
        for nombre in self._tags:
            if nombre not in nombres:
                nombres.append(nombre)
        return sorted(set(nombres), key=str.lower)

    def _refresh_tag_suggestions(self):
        nombres = self._picker_tag_names()
        self._tag_picker.blockSignals(True)
        self._tag_picker.clear()
        self._tag_picker.addItem("", "")
        for nombre in nombres:
            self._tag_picker.addItem(nombre, nombre)
        self._tag_picker.setCurrentIndex(0)
        self._tag_picker.blockSignals(False)

    def _render_tag_badges(self):
        while self._tags_layout.count() > 1:
            w = self._tags_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        estado_key = self._estado_visible()
        estado_chip = QFrame()
        estado_chip.setObjectName(
            TAG_STATUS_CHIP_NAMES.get(estado_key, "tagStatusChipReading")
        )
        estado_layout = QHBoxLayout(estado_chip)
        estado_layout.setContentsMargins(0, 0, 0, 0)
        estado_lbl = QLabel(etiqueta_de_estado(estado_key))
        estado_lbl.setObjectName("tagTextStatus")
        estado_layout.addWidget(estado_lbl)
        self._tags_layout.insertWidget(0, estado_chip)

        for nombre in self._tags:
            chip = QFrame()
            chip.setObjectName("tagChipCustom")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(6, 4, 4, 4)
            chip_layout.setSpacing(4)
            lbl = QLabel(nombre)
            lbl.setObjectName("tagText")
            btn_x = QPushButton()
            btn_x.setObjectName("tagRemove")
            btn_x.setToolTip(tr("collection.remove_tag"))
            set_button_icon(btn_x, "close", 12, TEXT_PRIMARY)
            btn_x.clicked.connect(lambda _, n=nombre: self._remove_tag(n))
            chip_layout.addWidget(lbl)
            chip_layout.addWidget(btn_x)
            self._tags_layout.insertWidget(self._tags_layout.count() - 1, chip)

        self._tags_scroll.setMinimumHeight(56)

    def _add_tag(self, nombre: str):
        nombre = (nombre or "").strip()
        if not nombre:
            return
        estado_key = resolver_estado_desde_etiqueta(nombre)
        if estado_key:
            self._estado_manual = estado_key
            self._render_tag_badges()
            self._refresh_tag_suggestions()
            return
        if any(t.lower() == nombre.lower() for t in self._tags):
            return
        self._tags.append(nombre)
        self._tags.sort(key=str.lower)
        self._render_tag_badges()
        self._refresh_tag_suggestions()

    def _remove_tag(self, nombre: str):
        self._tags = [t for t in self._tags if t.lower() != nombre.lower()]
        self._render_tag_badges()

    def _append_tag_from_picker(self):
        nombre = (self._tag_picker.currentText() or "").strip()
        if not nombre:
            return
        if nombre.lower() == tr("reading_status.auto").lower():
            self._estado_manual = None
            self._render_tag_badges()
            self._tag_picker.setCurrentIndex(0)
            self._tag_picker.clearEditText()
            return
        self._add_tag(nombre)
        self._tag_picker.setCurrentIndex(0)
        self._tag_picker.clearEditText()

    def _reemplazar_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            tr("books.select_pdf"),
            "",
            tr("books.pdf_filter"),
        )
        if archivo:
            self._archivo_reemplazo = archivo
            self.lbl_nombre_archivo.setText(os.path.basename(archivo))

    def configurar_eliminar(self, callback):
        self.btn_eliminar.show()
        self.btn_eliminar.clicked.connect(callback)

    def obtener_datos(self):
        return (
            self.titulo_input.text(),
            self.autor_input.text(),
            self.genero_input.text(),
            self.obtener_etiquetas(),
            self.obtener_estado_manual(),
        )

    def archivo_reemplazo(self):
        return self._archivo_reemplazo
