"""Diálogo modal para añadir o editar un libro."""

import os

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGridLayout, QFileDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt

from icons import app_icon, icon_label, set_button_icon
from i18n import tr
from styles import ACCENT_TEXT, TEXT_SECONDARY


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
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

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
        row_autor_genero.setSpacing(12)
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

        self._lbl_etiquetas = QLabel()
        self._lbl_etiquetas.setObjectName("fieldLabel")
        self.etiquetas_input = QLineEdit()
        self.etiquetas_input.setPlaceholderText("")
        root.addWidget(self._lbl_etiquetas)
        root.addWidget(self.etiquetas_input)

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

        self.retranslate_ui()

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
        self._lbl_etiquetas.setText(tr("book_dialog.field_tags"))
        self.etiquetas_input.setPlaceholderText(tr("book_dialog.tags_placeholder"))
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
            self.etiquetas_input.text(),
        )

    def archivo_reemplazo(self):
        return self._archivo_reemplazo
