import logging

import fitz
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox,
    QLineEdit, QLabel, QTextBrowser, QTextEdit, QScrollArea, QWidget,
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QImage, QPixmap

from crud import (
    actualizar_paginas_leidas, obtener_paginas_leidas,
    crear_nota, obtener_notas_por_libro, actualizar_nota, eliminar_nota,
    crear_marcador, obtener_marcadores_por_libro, eliminar_marcador,
    actualizar_marcador,
)
from i18n import tr

logger = logging.getLogger(__name__)

# Estilo reutilizable para los QMessageBox del visor.
_MSGBOX_STYLE = """
    QMessageBox { background-color: #0F3444; color: white; }
    QMessageBox QLabel { color: white; font-size: 14px; }
    QMessageBox QPushButton {
        background-color: #1A4D5B; color: white; border: 1px solid #2D7D8F;
        border-radius: 4px; padding: 8px 16px; font-size: 14px; min-width: 80px;
    }
    QMessageBox QPushButton:hover { background-color: #2D7D8F; }
    QMessageBox QPushButton:focus { outline: none; }
"""


def _mensaje(parent, icono, titulo, texto):
    """Muestra un QMessageBox con el estilo de la aplicación."""
    msg = QMessageBox(parent)
    msg.setIcon(icono)
    msg.setWindowTitle(titulo)
    msg.setText(texto)
    msg.setStyleSheet(_MSGBOX_STYLE)
    return msg.exec_()


class PDFViewer(QDialog):
    # Número de páginas a renderizar por encima/debajo de la zona visible.
    RENDER_BUFFER = 1

    def __init__(self, pdf_path, libro_id=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.libro_id = libro_id
        self.zoom_level = 1.0
        self.doc = None
        self.current_page = 0
        self.total_pages = 0

        # Placeholders de página y control de cuáles están renderizadas.
        self.page_labels = []
        self.page_sizes = []  # (ancho, alto) a zoom 1.0, en píxeles.
        self.rendered_pages = set()

        # Timer para guardar el progreso (evita escribir en cada scroll).
        self.save_timer = QTimer()
        self.save_timer.setInterval(1000)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_reading_progress)

        # Timer para renderizar tras el scroll (throttling).
        self.render_timer = QTimer()
        self.render_timer.setInterval(60)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render_visible_pages)

        self.setWindowTitle(tr("pdf.viewer_title"))
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("""
            QDialog { background-color: #1A4D5B; }
            QLabel#pageLabel {
                color: black; background-color: white;
                border: 1px solid #ddd; border-radius: 5px; margin: 10px;
            }
            QLabel { color: white; font-size: 14px; }
            QPushButton {
                background-color: #0F3444; color: white; border: none;
                padding: 8px 15px; border-radius: 3px;
            }
            QPushButton:hover { background-color: #518C7A; }
            QLineEdit {
                background-color: #0F3444; color: white; border: 1px solid #2D7D8F;
                border-radius: 3px; padding: 4px 8px; max-width: 60px;
            }
            QScrollArea { border: none; background-color: #1A4D5B; }
            QScrollBar:vertical {
                background-color: #0F3444; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #518C7A; border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ----- Barra de herramientas -----
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)

        self.page_input = QLineEdit()
        self.page_input.setToolTip(tr("pdf.go_to_page"))
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.returnPressed.connect(self._ir_a_pagina_desde_input)

        self.page_indicator = QLabel(tr("pdf.page_indicator", current=0, total=0))

        self.bookmark_btn = QPushButton(f"🔖 {tr('pdf.bookmarks')}")
        self.bookmark_btn.setToolTip(tr("pdf.bookmarks_tooltip"))
        self.bookmark_btn.clicked.connect(self.mostrar_marcadores)

        self.notes_btn = QPushButton(f"📝 {tr('pdf.notes')}")
        self.notes_btn.setToolTip(tr("pdf.notes_tooltip"))
        self.notes_btn.clicked.connect(self.mostrar_notas)

        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedWidth(50)
        self.fullscreen_btn.setToolTip(tr("pdf.fullscreen_tooltip"))
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        self._goto_label = QLabel(tr("pdf.go_to_label"))
        toolbar.addWidget(self._goto_label)
        toolbar.addWidget(self.page_input)
        toolbar.addWidget(self.page_indicator)
        toolbar.addStretch()
        toolbar.addWidget(self.bookmark_btn)
        toolbar.addWidget(self.notes_btn)
        toolbar.addWidget(self.fullscreen_btn)
        layout.addLayout(toolbar)

        # ----- Área de visualización -----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.scroll_area)

        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.setSpacing(0)
        self.page_layout.setAlignment(Qt.AlignHCenter)
        self.scroll_area.setWidget(self.page_container)

        self.scroll_area.viewport().installEventFilter(self)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

        # Cargar el PDF y renderizar las primeras páginas visibles.
        if self.load_pdf():
            QTimer.singleShot(0, self.render_visible_pages)
            if self.libro_id:
                self.restore_reading_progress()

    # ------------------------------------------------------------------
    # Carga y renderizado perezoso
    # ------------------------------------------------------------------
    def load_pdf(self):
        """Abre el PDF y construye los placeholders de página (sin renderizar)."""
        import os

        if not os.path.exists(self.pdf_path):
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.file_not_found", path=self.pdf_path))
            return False

        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            logger.exception("Error al abrir el PDF %s: %s", self.pdf_path, e)
            _mensaje(self, QMessageBox.Critical, tr("common.error"),
                     tr("pdf.open_failed"))
            self.doc = None
            return False

        self.total_pages = self.doc.page_count
        if self.total_pages == 0:
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.empty"))
            return False

        self._construir_placeholders()
        self.page_indicator.setText(
            tr("pdf.page_indicator", current=1, total=self.total_pages)
        )
        return True

    def _construir_placeholders(self):
        """Crea un QLabel vacío por página con el tamaño correcto a zoom 1.0."""
        self._limpiar_layout()
        self.page_labels = []
        self.page_sizes = []
        self.rendered_pages = set()

        for page_num in range(self.total_pages):
            rect = self.doc.load_page(page_num).rect
            self.page_sizes.append((rect.width, rect.height))

            label = QLabel()
            label.setObjectName("pageLabel")
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(int(rect.width * self.zoom_level),
                               int(rect.height * self.zoom_level))
            self.page_layout.addWidget(label)
            self.page_labels.append(label)

    def _limpiar_layout(self):
        while self.page_layout.count():
            item = self.page_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_page(self, page_num):
        if page_num in self.rendered_pages or not self.doc:
            return
        try:
            page = self.doc.load_page(page_num)
            matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=matrix)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                         QImage.Format_RGB888)
            self.page_labels[page_num].setPixmap(QPixmap.fromImage(img))
            self.rendered_pages.add(page_num)
        except Exception as e:
            logger.exception("Error al renderizar la página %s: %s", page_num, e)

    def _unrender_page(self, page_num):
        if page_num not in self.rendered_pages:
            return
        label = self.page_labels[page_num]
        label.clear()
        w, h = self.page_sizes[page_num]
        label.setFixedSize(int(w * self.zoom_level), int(h * self.zoom_level))
        self.rendered_pages.discard(page_num)

    def _rango_visible(self):
        """Devuelve (primera, ultima) página visible en el viewport."""
        if not self.page_labels:
            return (0, -1)
        top = self.scroll_area.verticalScrollBar().value()
        bottom = top + self.scroll_area.viewport().height()

        primera, ultima = None, None
        for i, label in enumerate(self.page_labels):
            y = label.y()
            if y + label.height() >= top and y <= bottom:
                if primera is None:
                    primera = i
                ultima = i
        if primera is None:
            # Ninguna calculada aún (layout sin resolver): usar la actual.
            return (self.current_page, self.current_page)
        return (primera, ultima)

    def render_visible_pages(self):
        if not self.doc:
            return
        primera, ultima = self._rango_visible()
        inicio = max(0, primera - self.RENDER_BUFFER)
        fin = min(self.total_pages - 1, ultima + self.RENDER_BUFFER)

        deseadas = set(range(inicio, fin + 1))
        for page_num in deseadas:
            self._render_page(page_num)
        # Liberar memoria de páginas fuera del rango.
        for page_num in list(self.rendered_pages):
            if page_num not in deseadas:
                self._unrender_page(page_num)

    # ------------------------------------------------------------------
    # Zoom, scroll y navegación
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.zoom_level = min(5.0, self.zoom_level * 1.2)
                else:
                    self.zoom_level = max(0.2, self.zoom_level / 1.2)
                self._aplicar_zoom()
                return True
        return super().eventFilter(obj, event)

    def _aplicar_zoom(self):
        """Reajusta tamaños al nuevo zoom y vuelve a renderizar lo visible."""
        for i, label in enumerate(self.page_labels):
            w, h = self.page_sizes[i]
            label.clear()
            label.setFixedSize(int(w * self.zoom_level), int(h * self.zoom_level))
        self.rendered_pages = set()
        self.render_visible_pages()

    def on_scroll(self):
        if not self.doc:
            return
        primera, ultima = self._rango_visible()
        if primera is not None and primera != self.current_page:
            self.current_page = primera
            self.page_indicator.setText(
                tr("pdf.page_indicator", current=primera + 1, total=self.total_pages)
            )
            if self.libro_id:
                self.save_timer.start()
        self.render_timer.start()

    def _ir_a_pagina_desde_input(self):
        texto = self.page_input.text().strip()
        if not texto.isdigit():
            return
        numero = int(texto) - 1  # El usuario cuenta desde 1.
        if 0 <= numero < self.total_pages:
            self.scroll_to_page(numero)
        else:
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.invalid_page", total=self.total_pages))

    def scroll_to_page(self, page_num):
        try:
            if 0 <= page_num < len(self.page_labels):
                self._render_page(page_num)
                self.scroll_area.ensureWidgetVisible(self.page_labels[page_num])
                self.render_timer.start()
        except Exception as e:
            logger.exception("Error al hacer scroll a la página %s: %s", page_num, e)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ------------------------------------------------------------------
    # Progreso de lectura
    # ------------------------------------------------------------------
    def save_reading_progress(self):
        if self.libro_id:
            try:
                actualizar_paginas_leidas(self.libro_id, self.current_page)
            except Exception as e:
                logger.exception("Error al guardar progreso: %s", e)

    def restore_reading_progress(self):
        try:
            pagina = obtener_paginas_leidas(self.libro_id)
            if pagina and pagina > 0:
                QTimer.singleShot(300, lambda: self.scroll_to_page(pagina))
        except Exception as e:
            logger.exception("Error al restaurar progreso: %s", e)

    def closeEvent(self, event):
        if self.libro_id:
            self.save_reading_progress()
        if self.doc:
            self.doc.close()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Diálogos de notas y marcadores
    # ------------------------------------------------------------------
    def mostrar_notas(self):
        if not self.libro_id:
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.notes_need_id"))
            return
        NotasDialog(self.libro_id, self).exec_()

    def mostrar_marcadores(self):
        if not self.libro_id:
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.bookmarks_need_id"))
            return
        MarcadoresDialog(self, self.libro_id).exec_()


class MarcadoresDialog(QDialog):
    """Diálogo para gestionar los marcadores de un libro."""

    def __init__(self, viewer, libro_id):
        super().__init__(viewer)
        self.viewer = viewer
        self.libro_id = libro_id
        self.setWindowTitle(tr("pdf.bookmarks_title"))
        self.setMinimumSize(420, 520)
        self.setStyleSheet("""
            QDialog { background-color: #1A4D5B; color: white; }
            QListWidget {
                background-color: #0F3444; border: 1px solid #518C7A;
                border-radius: 5px; padding: 5px; color: white; font-size: 14px;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #518C7A; }
            QListWidget::item:selected { background-color: #518C7A; }
            QPushButton {
                background-color: #0F3444; color: white; border: 1px solid #518C7A;
                border-radius: 15px; padding: 8px 15px; font-size: 14px;
            }
            QPushButton:hover { background-color: #518C7A; }
            QLabel { font-size: 14px; }
            QLineEdit {
                background-color: #0F3444; color: white; border: 1px solid #518C7A;
                border-radius: 8px; padding: 8px 10px; font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("pdf.bookmarks_header")))

        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(self._ir_al_marcador)
        layout.addWidget(self.lista)

        btns = QHBoxLayout()
        add_btn = QPushButton(f"🔖 {tr('pdf.add_bookmark')}")
        add_btn.clicked.connect(self._add_marcador)
        rename_btn = QPushButton(f"✏️ {tr('pdf.edit_bookmark')}")
        rename_btn.clicked.connect(self._rename_marcador)
        goto_btn = QPushButton(tr("pdf.goto"))
        goto_btn.clicked.connect(self._ir_al_marcador)
        del_btn = QPushButton(f"🗑️ {tr('pdf.delete')}")
        del_btn.clicked.connect(self._eliminar_marcador)
        btns.addWidget(add_btn)
        btns.addWidget(rename_btn)
        btns.addWidget(goto_btn)
        btns.addWidget(del_btn)
        layout.addLayout(btns)

        self._cargar()

    def _bookmark_label(self, pagina, etiqueta=None):
        page_num = pagina + 1
        if etiqueta:
            return tr("pdf.bookmark_item", name=etiqueta, page=page_num)
        return tr("pdf.page_item", page=page_num, label="")

    def _prompt_bookmark_name(self, title_key, pagina, default=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr(title_key))
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(self.styleSheet())

        form = QVBoxLayout(dialog)
        form.addWidget(QLabel(tr("pdf.bookmark_page_info", page=pagina + 1)))
        form.addWidget(QLabel(tr("pdf.bookmark_name_label")))
        name_input = QLineEdit()
        name_input.setText(default)
        name_input.setPlaceholderText(tr("pdf.bookmark_name_placeholder"))
        form.addWidget(name_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton(tr("common.save"))
        save_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        form.addLayout(btn_row)

        if dialog.exec_() != QDialog.Accepted:
            return None
        return name_input.text().strip()

    def _cargar(self):
        self.lista.clear()
        for m in obtener_marcadores_por_libro(self.libro_id):
            item = QListWidgetItem(self._bookmark_label(m.pagina, m.etiqueta))
            item.setData(Qt.UserRole, m.id_marcador)
            item.setData(Qt.UserRole + 1, m.pagina)
            item.setData(Qt.UserRole + 2, m.etiqueta or "")
            self.lista.addItem(item)

    def _add_marcador(self):
        pagina = self.viewer.current_page
        nombre = self._prompt_bookmark_name("pdf.bookmark_add_title", pagina)
        if nombre is None:
            return
        if crear_marcador(self.libro_id, pagina, etiqueta=nombre or None):
            self._cargar()
        else:
            _mensaje(self, QMessageBox.Warning, tr("common.error"),
                     tr("pdf.bookmark_failed"))

    def _rename_marcador(self):
        item = self.lista.currentItem()
        if not item:
            return
        pagina = item.data(Qt.UserRole + 1)
        actual = item.data(Qt.UserRole + 2) or ""
        nombre = self._prompt_bookmark_name(
            "pdf.bookmark_edit_title", pagina, default=actual
        )
        if nombre is None:
            return
        if actualizar_marcador(item.data(Qt.UserRole), nombre or None):
            self._cargar()

    def _ir_al_marcador(self):
        item = self.lista.currentItem()
        if not item:
            return
        pagina = item.data(Qt.UserRole + 1)
        self.viewer.scroll_to_page(pagina)
        self.accept()

    def _eliminar_marcador(self):
        item = self.lista.currentItem()
        if not item:
            return
        if eliminar_marcador(item.data(Qt.UserRole)):
            self._cargar()


class NotasDialog(QDialog):
    """Diálogo para ver y agregar notas"""
    def __init__(self, libro_id, parent=None):
        super().__init__(parent)
        self.libro_id = libro_id
        self.setWindowTitle(tr("pdf.notes_title"))
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            QDialog {
                background-color: #1A4D5B;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget {
                background-color: #0F3444;
                border: 1px solid #518C7A;
                border-radius: 5px;
                padding: 5px;
                color: #FFFFFF;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #518C7A;
                background-color: #0F3444;
            }
            QListWidget::item:selected {
                background-color: #518C7A;
                color: white;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #3f6f75;
            }
            QPushButton {
                background-color: #0F3444;
                color: white;
                border: 1px solid #518C7A;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #518C7A;
            }
            QPushButton:pressed {
                background-color: #3f6f75;
            }
            QTextEdit, QTextBrowser {
                background-color: #0F3444;
                color: #FFFFFF;
                border: 1px solid #518C7A;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
        """)

        main_layout = QHBoxLayout(self)

        # Panel izquierdo - Lista de notas
        left_panel = QVBoxLayout()

        title_label = QLabel(tr("pdf.your_notes"))
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #7DD6A6; padding: 10px 0;")
        left_panel.addWidget(title_label)

        self.notas_list = QListWidget()
        self.notas_list.setMinimumWidth(250)
        self.notas_list.itemClicked.connect(self.mostrar_nota_seleccionada)
        left_panel.addWidget(self.notas_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(f"➕ {tr('pdf.new_note')}")
        self.add_btn.clicked.connect(self.agregar_nota)
        self.delete_btn = QPushButton(f"🗑️ {tr('pdf.delete')}")
        self.delete_btn.clicked.connect(self.eliminar_nota)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        left_panel.addLayout(btn_layout)

        # Panel derecho - Vista previa de la nota
        right_panel = QVBoxLayout()

        self.note_title = QLabel(tr("pdf.select_note"))
        self.note_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #7DD6A6; padding: 10px 0;")

        self.note_date = QLabel("")
        self.note_date.setStyleSheet(
            "color: #AAAAAA; font-size: 12px; padding-bottom: 10px;")

        self.note_content = QTextBrowser()
        self.note_content.setReadOnly(True)

        self.edit_btn = QPushButton(f"✏️ {tr('pdf.edit_note')}")
        self.edit_btn.clicked.connect(self.editar_nota_actual)
        self.edit_btn.setVisible(False)

        right_panel.addWidget(self.note_title)
        right_panel.addWidget(self.note_date)
        right_panel.addWidget(self.note_content, 1)
        right_panel.addWidget(self.edit_btn, 0, Qt.AlignRight)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        self.cargar_notas()
        self.notas_list.itemDoubleClicked.connect(self.editar_nota_actual)

    def cargar_notas(self):
        self.notas_list.clear()
        self.notas = obtener_notas_por_libro(self.libro_id)

        for nota in self.notas:
            fecha_formateada = nota.fecha_creacion.strftime('%d %b %Y %H:%M')
            item = QListWidgetItem(f"{nota.titulo}")
            item.setData(Qt.UserRole, nota.id_nota)
            item.setData(Qt.UserRole + 1, nota)
            item.setToolTip(tr("pdf.note_created", date=fecha_formateada))
            self.notas_list.addItem(item)

        if not self.notas:
            self.note_title.setText(tr("pdf.no_notes"))
            self.note_date.clear()
            self.note_content.clear()
            self.edit_btn.setVisible(False)

    def agregar_nota(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("pdf.new_note_title"))
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(tr("pdf.note_title_label")))
        titulo_edit = QLineEdit()
        titulo_edit.setPlaceholderText(tr("pdf.note_title_placeholder"))
        layout.addWidget(titulo_edit)

        layout.addWidget(QLabel(tr("pdf.note_content_label")))
        contenido_edit = QTextEdit()
        contenido_edit.setPlaceholderText(tr("pdf.note_content_placeholder"))
        contenido_edit.setMinimumHeight(200)
        layout.addWidget(contenido_edit)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton(tr("common.save"))
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            titulo = titulo_edit.text().strip()
            contenido = contenido_edit.toPlainText().strip()

            if not titulo:
                _mensaje(self, QMessageBox.Warning, tr("common.error"),
                         tr("pdf.note_title_empty"))
                return

            try:
                crear_nota(titulo, self.libro_id, contenido)
                self.cargar_notas()
                if self.notas_list.count() > 0:
                    self.notas_list.setCurrentRow(0)
            except Exception as e:
                logger.exception("Error al crear la nota: %s", e)
                _mensaje(self, QMessageBox.Critical, tr("common.error"),
                         tr("pdf.note_create_error", error=str(e)))

    def mostrar_nota_seleccionada(self, item):
        if not item:
            return
        nota = item.data(Qt.UserRole + 1)
        if not nota:
            return
        self.note_title.setText(nota.titulo)
        self.note_date.setText(
            tr("pdf.note_created", date=nota.fecha_creacion.strftime('%d/%m/%Y %H:%M')))
        self.note_content.setPlainText(nota.contenido)
        self.edit_btn.setVisible(True)
        self.current_note_id = nota.id_nota

    def editar_nota_actual(self):
        current_item = self.notas_list.currentItem()
        if current_item:
            self.editar_nota(current_item)

    def editar_nota(self, item):
        nota = item.data(Qt.UserRole + 1)
        if not nota:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("pdf.edit_note_title", title=nota.titulo))
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dialog)
        titulo_edit = QLineEdit()
        titulo_edit.setText(nota.titulo)
        layout.addWidget(QLabel(tr("pdf.note_title_label")))
        layout.addWidget(titulo_edit)

        contenido_edit = QTextEdit()
        contenido_edit.setPlainText(nota.contenido)
        contenido_edit.setMinimumHeight(200)
        layout.addWidget(QLabel(tr("pdf.note_content_label")))
        layout.addWidget(contenido_edit)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton(tr("pdf.save_changes"))
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            nuevo_titulo = titulo_edit.text().strip()
            nuevo_contenido = contenido_edit.toPlainText().strip()

            if not nuevo_titulo:
                _mensaje(self, QMessageBox.Warning, tr("common.error"),
                         tr("pdf.note_title_empty"))
                return

            try:
                if nuevo_titulo != nota.titulo or nuevo_contenido != nota.contenido:
                    actualizar_nota(nota.id_nota, nuevo_titulo, nuevo_contenido)
                    self.cargar_notas()
                    for i in range(self.notas_list.count()):
                        current_item = self.notas_list.item(i)
                        if current_item.data(Qt.UserRole) == nota.id_nota:
                            self.notas_list.setCurrentItem(current_item)
                            self.mostrar_nota_seleccionada(current_item)
                            break
            except Exception as e:
                logger.exception("Error al actualizar la nota: %s", e)
                _mensaje(self, QMessageBox.Critical, tr("common.error"),
                         tr("pdf.note_update_error", error=str(e)))

    def eliminar_nota(self):
        current_item = self.notas_list.currentItem()
        if not current_item:
            return
        nota_id = current_item.data(Qt.UserRole)
        if not nota_id:
            return

        titulo_nota = current_item.text()
        mensaje = tr("pdf.delete_note_confirm", title=titulo_nota)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(tr("books.delete_confirm_title"))
        msg_box.setText(tr("pdf.delete_note_title"))
        msg_box.setInformativeText(mensaje)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(_MSGBOX_STYLE)

        if msg_box.exec_() == QMessageBox.Yes:
            try:
                eliminar_nota(nota_id)
                self.cargar_notas()
                self.note_title.setText(tr("pdf.select_note"))
                self.note_date.clear()
                self.note_content.clear()
                self.edit_btn.setVisible(False)
            except Exception as e:
                logger.exception("Error al eliminar la nota: %s", e)
                _mensaje(self, QMessageBox.Critical, tr("common.error"),
                         tr("pdf.note_delete_error", error=str(e)))
