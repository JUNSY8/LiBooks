import logging
import os

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QFileDialog, QMessageBox,
    QDialog, QScrollArea, QStackedWidget,
)
from PyQt5.QtCore import Qt, QSize

from crud import crear_libro_pdf
from pdf_viewer import PDFViewer
from datos import Datos
from dialogs import ColeccionDialog
from settings_dialog import SettingsDialog
from icons import app_icon, icon_label, set_button_icon
from i18n import tr, register_language_callback
from styles import msgbox_danger_button_style, ACCENT_TEXT, TEXT_SECONDARY

logger = logging.getLogger(__name__)


class BibliotecaApp(QWidget):
    """Ventana principal de la biblioteca digital."""

    def __init__(self):
        super().__init__()
        self.setWindowIcon(app_icon())
        self.setGeometry(100, 100, 1200, 720)
        self._nav_buttons = {}
        self._vista_actual = "libros"
        self._book_count = 0
        register_language_callback(self.retranslate_ui)
        self.initUI()

    # ── Construcción de la UI ──────────────────────────────────────────

    def initUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_sidebar(main_layout)
        self._build_main_content(main_layout)

        self.cargar_pdf_desde_db()
        self._set_nav_active("libros")
        self.retranslate_ui()

    def retranslate_ui(self):
        """Actualiza textos al cambiar idioma."""
        self.setWindowTitle(tr("app.window_title"))
        self._lbl_subtitle.setText(tr("app.subtitle"))
        set_button_icon(
            self._nav_buttons["libros"], "books", 18, TEXT_SECONDARY, tr("nav.my_books")
        )
        self._col_lbl.setText(tr("nav.collections"))
        self._btn_add_col.setToolTip(tr("nav.new_collection"))
        set_button_icon(
            self._btn_settings, "settings", 18, TEXT_SECONDARY, tr("nav.settings")
        )
        self.btn_atras.setText(tr("nav.back"))
        self.search_bar.setPlaceholderText(tr("books.search_placeholder"))
        set_button_icon(self._btn_add, "plus", 16, ACCENT_TEXT, tr("books.add"))
        self.empty_state.setText(tr("books.empty_state"))
        self._actualizar_contador(self._book_count)
        filtro = self.search_bar.text().strip()
        if filtro or self._book_count > 0:
            self.cargar_pdf_desde_db(filtro=filtro or None)

    def mostrar_ajustes(self):
        SettingsDialog(self).exec_()

    def _build_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 24, 16, 24)
        sl.setSpacing(4)

        # Marca
        brand = QHBoxLayout()
        brand_box = QFrame()
        brand_box.setObjectName("dialogIconBox")
        brand_box.setFixedSize(44, 44)
        bl = QHBoxLayout(brand_box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(icon_label("app", 32))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("LiBooks")
        title.setObjectName("appTitle")
        subtitle = QLabel()
        subtitle.setObjectName("appSubtitle")
        self._lbl_subtitle = subtitle
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        brand.addWidget(brand_box)
        brand.addLayout(brand_text, 1)
        sl.addLayout(brand)
        sl.addSpacing(20)

        # Navegación
        self._nav_buttons["libros"] = self._make_nav_btn(
            "", "libros", self.mostrar_todos_los_libros, "books"
        )
        sl.addWidget(self._nav_buttons["libros"])

        # Colecciones con botón +
        col_header = QHBoxLayout()
        col_header.setContentsMargins(8, 8, 4, 4)
        col_lbl = QLabel()
        col_lbl.setObjectName("fieldLabel")
        self._col_lbl = col_lbl
        btn_add_col = QPushButton()
        btn_add_col.setObjectName("addCollectionBtn")
        self._btn_add_col = btn_add_col
        set_button_icon(btn_add_col, "collection", 16)
        btn_add_col.setToolTip("Nueva colección")
        btn_add_col.clicked.connect(self.mostrar_formulario_coleccion)
        col_header.addWidget(col_lbl)
        col_header.addStretch()
        col_header.addWidget(btn_add_col)
        sl.addLayout(col_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.colecciones_container = QWidget()
        self.colecciones_layout = QVBoxLayout(self.colecciones_container)
        self.colecciones_layout.setContentsMargins(0, 0, 0, 0)
        self.colecciones_layout.setSpacing(2)
        scroll.setWidget(self.colecciones_container)
        sl.addWidget(scroll, 1)

        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFrameShape(QFrame.HLine)
        sl.addWidget(divider)

        btn_ajustes = QPushButton()
        btn_ajustes.setObjectName("navButton")
        self._btn_settings = btn_ajustes
        btn_ajustes.clicked.connect(self.mostrar_ajustes)
        sl.addWidget(btn_ajustes)

        self.actualizar_lista_colecciones = self._crear_actualizador_colecciones()
        parent_layout.addWidget(sidebar)

    def _make_nav_btn(self, text, key, callback, icon_name=None):
        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setProperty("active", False)
        if icon_name:
            set_button_icon(btn, icon_name, 18, TEXT_SECONDARY, text)
        btn.clicked.connect(lambda: (self._set_nav_active(key), callback()))
        return btn

    def _set_nav_active(self, key):
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _build_main_content(self, parent_layout):
        self.panel_derecho = QFrame()
        self.panel_derecho.setObjectName("mainContent")
        rl = QVBoxLayout(self.panel_derecho)
        rl.setContentsMargins(32, 28, 32, 28)
        rl.setSpacing(16)

        self.contenido_dinamico = QStackedWidget()
        self.pagina_libros = QWidget()
        libros_layout = QVBoxLayout(self.pagina_libros)
        libros_layout.setContentsMargins(0, 0, 0, 0)
        libros_layout.setSpacing(16)

        # Cabecera: atrás + búsqueda + añadir
        header = QHBoxLayout()
        header.setSpacing(12)

        self.btn_atras = QPushButton()
        self.btn_atras.setObjectName("ghostButton")
        self.btn_atras.hide()
        self.btn_atras.clicked.connect(self.mostrar_todos_los_libros)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Buscar libros...")
        self.search_bar.returnPressed.connect(self.realizar_busqueda)
        self.search_bar.textChanged.connect(self.filtrar_libros)

        add_btn = QPushButton()
        add_btn.setObjectName("primaryButton")
        self._btn_add = add_btn
        set_button_icon(add_btn, "plus", 16, ACCENT_TEXT, "")
        add_btn.clicked.connect(self.agregar_libro_pdf)

        header.addWidget(self.btn_atras)
        header.addWidget(self.search_bar, 1)
        header.addWidget(add_btn)
        libros_layout.addLayout(header)

        # Contador
        self.lbl_count = QLabel()
        self.lbl_count.setObjectName("sectionCount")
        libros_layout.addWidget(self.lbl_count)

        # Lista de libros
        self.pdf_list = QListWidget()
        self.pdf_list.setObjectName("bookList")
        self.pdf_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.pdf_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pdf_list.itemDoubleClicked.connect(self.abrir_pdf)
        libros_layout.addWidget(self.pdf_list, 1)

        # Estado vacío
        self.empty_state = QLabel()
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setAlignment(Qt.AlignCenter)
        libros_layout.addWidget(self.empty_state)

        self.contenido_dinamico.addWidget(self.pagina_libros)
        rl.addWidget(self.contenido_dinamico)
        parent_layout.addWidget(self.panel_derecho, 1)

    def _crear_actualizador_colecciones(self):
        def actualizar():
            while self.colecciones_layout.count():
                item = self.colecciones_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            from crud import obtener_colecciones
            from models import Coleccion

            try:
                for coleccion in obtener_colecciones():
                    if not isinstance(coleccion, Coleccion):
                        continue
                    row = QWidget()
                    rl = QHBoxLayout(row)
                    rl.setContentsMargins(0, 0, 0, 0)
                    rl.setSpacing(4)

                    btn = QPushButton(coleccion.nombre)
                    btn.setObjectName("collectionItem")
                    filtros = {
                        "id_coleccion": coleccion.id_coleccion,
                        "libro_id": (
                            coleccion.libros[0].id_libro
                            if coleccion.libros else None
                        ),
                        "autor_id": getattr(coleccion, "filtro_autor_id", None),
                        "genero_id": getattr(coleccion, "filtro_genero_id", None),
                    }
                    btn.clicked.connect(
                        lambda _, f=filtros: self.aplicar_filtros_coleccion(f)
                    )

                    btn_del = QPushButton("×")
                    btn_del.setObjectName("collectionDelete")
                    btn_del.clicked.connect(
                        lambda _, cid=coleccion.id_coleccion, n=coleccion.nombre:
                        self.confirmar_eliminar_coleccion(cid, n)
                    )

                    rl.addWidget(btn, 1)
                    rl.addWidget(btn_del)
                    self.colecciones_layout.addWidget(row)

                self.colecciones_layout.addStretch()
            except Exception as e:
                logger.exception("Error al cargar colecciones: %s", e)

        actualizar()
        return actualizar

    def _actualizar_contador(self, n):
        self._book_count = n
        if n == 0:
            self.lbl_count.setText(tr("books.count_zero"))
        elif n == 1:
            self.lbl_count.setText(tr("books.count_one", n=n))
        else:
            self.lbl_count.setText(tr("books.count_many", n=n))
        self.empty_state.setVisible(n == 0)

    # ── Modales ────────────────────────────────────────────────────────

    def mostrar_formulario_coleccion(self):
        dialog = ColeccionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.actualizar_lista_colecciones()

    def agregar_libro_pdf(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, tr("books.select_pdf"), "", tr("books.pdf_filter")
        )
        if not archivo:
            return

        try:
            dialogo = Datos(self, modo="añadir", archivo=archivo)
            nombre = os.path.splitext(os.path.basename(archivo))[0]
            dialogo.titulo_input.setText(nombre)

            if dialogo.exec_() == QDialog.Accepted:
                titulo, autor, genero = dialogo.obtener_datos()
                if crear_libro_pdf(
                    archivo,
                    titulo=titulo,
                    nombre_autor=autor,
                    nombre_genero=genero,
                    paginas_leidas=0,
                ):
                    self.cargar_pdf_desde_db()
                    QMessageBox.information(
                        self, tr("common.success"), tr("books.added")
                    )
                else:
                    QMessageBox.warning(
                        self, tr("common.error"), tr("books.add_failed")
                    )
        except Exception as e:
            QMessageBox.critical(
                self, tr("common.error"), tr("books.add_error", error=e)
            )

    def mostrar_dialogo_actualizar(self, id_libro):
        libro = self.obtener_libro(id_libro)
        if not libro:
            QMessageBox.warning(self, tr("common.error"), tr("books.not_found"))
            return

        from db import PDF_FOLDER
        ruta = (
            os.path.join(PDF_FOLDER, libro.archivo_pdf)
            if libro.archivo_pdf else None
        )

        dialog = Datos(self, modo="editar", archivo=ruta, libro_id=id_libro)
        dialog.titulo_input.setText(libro.titulo)
        dialog.autor_input.setText(libro.autor or "")
        dialog.genero_input.setText(libro.genero or "")

        dialog.boton_guardar.clicked.disconnect()
        dialog.boton_guardar.clicked.connect(
            lambda: self.guardar_actualizacion(id_libro, dialog)
        )
        dialog.configurar_eliminar(
            lambda: (dialog.reject(), self.confirmar_eliminar_libro(id_libro))
        )
        dialog.exec_()

    def guardar_actualizacion(self, id_libro, dialog):
        try:
            from crud import actualizar_libro
            titulo = dialog.titulo_input.text()
            autor = dialog.autor_input.text()
            genero = dialog.genero_input.text()
            actualizar_libro(
                id_libro,
                titulo=titulo,
                nombre_autor=autor,
                nombre_genero=genero or None,
            )
            self.cargar_pdf_desde_db()
            QMessageBox.information(
                self, tr("common.success"), tr("books.updated")
            )
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(
                self, tr("common.error"), tr("books.update_error", error=e)
            )

    # ── Libros ─────────────────────────────────────────────────────────

    def limpiar_libros(self):
        if hasattr(self, "pdf_list") and self.pdf_list:
            self.pdf_list.clear()

    def cargar_pdf_desde_db(self, filtro=None):
        try:
            from crud import obtener_libros
            from db import PDF_FOLDER

            self.limpiar_libros()
            libros = obtener_libros()
            validos = []

            for libro in libros:
                ruta = None
                if getattr(libro, "ruta_archivo", None):
                    ruta = libro.ruta_archivo
                elif getattr(libro, "archivo_pdf", None):
                    ruta = os.path.join(PDF_FOLDER, libro.archivo_pdf)
                if ruta and os.path.exists(ruta):
                    validos.append(libro)

            if filtro and filtro.strip():
                f = filtro.lower()
                validos = [
                    lb for lb in validos
                    if f in (lb.titulo or "").lower()
                    or f in (lb.autor.nombre if lb.autor else "").lower()
                    or f in (lb.genero.nombre if lb.genero else "").lower()
                ]

            for libro in validos:
                self.agregar_libro_a_lista(libro)

            self._actualizar_contador(len(validos))
        except Exception as e:
            logger.exception("Error al cargar PDFs: %s", e)
            QMessageBox.critical(
                self, tr("common.error"), tr("books.load_error", error=e)
            )

    def agregar_libro_a_lista(self, libro):
        try:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 76))

            card = QFrame()
            card.setObjectName("bookCard")
            layout = QHBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(14)

            # Icono
            icon_box = QFrame()
            icon_box.setObjectName("bookIconBox")
            ib_l = QHBoxLayout(icon_box)
            ib_l.setContentsMargins(0, 0, 0, 0)
            ib_l.addWidget(icon_label("book", 32))

            # Info
            info = QVBoxLayout()
            info.setSpacing(2)
            titulo = getattr(libro, "titulo", None) or tr("books.no_title")
            titulo_lbl = QLabel(titulo)
            titulo_lbl.setObjectName("bookTitle")
            autor_nombre = libro.autor.nombre if getattr(libro, "autor", None) else ""
            autor_lbl = QLabel(autor_nombre or tr("books.unknown_author"))
            autor_lbl.setObjectName("bookAuthor")
            info.addWidget(titulo_lbl)
            info.addWidget(autor_lbl)

            # Acciones
            actions = QHBoxLayout()
            actions.setSpacing(8)
            btn_edit = QPushButton()
            btn_edit.setObjectName("iconButton")
            btn_edit.setToolTip(tr("books.edit_tooltip"))
            set_button_icon(btn_edit, "edit", 20)
            btn_del = QPushButton()
            btn_del.setObjectName("iconButtonDanger")
            btn_del.setToolTip(tr("books.delete_tooltip"))
            set_button_icon(btn_del, "trash", 20)

            if hasattr(libro, "id_libro"):
                btn_edit.clicked.connect(
                    lambda _, lid=libro.id_libro: self.mostrar_dialogo_actualizar(lid)
                )
                btn_del.clicked.connect(
                    lambda _, lid=libro.id_libro: self.confirmar_eliminar_libro(lid)
                )

            actions.addWidget(btn_edit)
            actions.addWidget(btn_del)

            layout.addWidget(icon_box)
            layout.addLayout(info, 1)
            layout.addLayout(actions)

            self.pdf_list.addItem(item)
            self.pdf_list.setItemWidget(item, card)

            if hasattr(libro, "id_libro"):
                item.setData(Qt.UserRole + 1, libro.id_libro)

            ruta_pdf = None
            if getattr(libro, "ruta_archivo", None):
                ruta_pdf = libro.ruta_archivo
            elif getattr(libro, "archivo_pdf", None):
                from db import PDF_FOLDER
                ruta_pdf = os.path.join(PDF_FOLDER, libro.archivo_pdf)
            item.setData(Qt.UserRole, ruta_pdf)

        except Exception as e:
            logger.exception("Error al agregar libro: %s", e)

    def abrir_pdf(self, item):
        try:
            if not item:
                return
            ruta = item.data(Qt.UserRole)
            libro_id = item.data(Qt.UserRole + 1)
            if not ruta or not os.path.exists(ruta):
                QMessageBox.warning(
                    self, tr("common.error"), tr("books.pdf_not_found")
                )
                return
            PDFViewer(ruta, libro_id).exec_()
        except Exception as e:
            logger.exception("Error al abrir PDF: %s", e)
            QMessageBox.critical(
                self, tr("common.error"), tr("books.open_error", error=e)
            )

    def obtener_libro(self, id_libro):
        try:
            from crud import obtener_libros
            libro = next((l for l in obtener_libros() if l.id_libro == id_libro), None)
            if libro:
                return type("Libro", (object,), {
                    "id_libro": libro.id_libro,
                    "titulo": libro.titulo,
                    "autor": libro.autor.nombre if libro.autor else None,
                    "genero": libro.genero.nombre if libro.genero else None,
                    "archivo_pdf": libro.archivo_pdf,
                })()
        except Exception as e:
            logger.exception("Error al obtener libro: %s", e)
        return None

    # ── Colecciones y filtros ──────────────────────────────────────────

    def mostrar_todos_los_libros(self):
        self.btn_atras.hide()
        self.cargar_pdf_desde_db()

    def aplicar_filtros_coleccion(self, filtros):
        from crud import obtener_libros, obtener_libros_en_coleccion

        if filtros.get("id_coleccion"):
            libros = obtener_libros_en_coleccion(filtros["id_coleccion"])
        else:
            libros = obtener_libros()
            if filtros.get("libro_id"):
                libros = [l for l in libros if l.id_libro == filtros["libro_id"]]
            if filtros.get("autor_id"):
                libros = [l for l in libros if l.autor and l.autor.id_autor == filtros["autor_id"]]
            if filtros.get("genero_id"):
                libros = [l for l in libros if l.genero and l.genero.id_genero == filtros["genero_id"]]

        self.limpiar_libros()
        for libro in libros:
            self.agregar_libro_a_lista(libro)
        self._actualizar_contador(self.pdf_list.count())
        self.btn_atras.show()

    def filtrar_libros(self, texto):
        self.cargar_pdf_desde_db(filtro=texto)

    def realizar_busqueda(self):
        self.filtrar_libros(self.search_bar.text())

    # ── Confirmaciones ─────────────────────────────────────────────────

    def _confirmar_eliminacion(self, titulo, mensaje, info=""):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        if info:
            msg.setInformativeText(info)
        si = msg.addButton(tr("common.delete_yes"), QMessageBox.YesRole)
        msg.addButton(tr("common.cancel"), QMessageBox.NoRole)
        si.setStyleSheet(msgbox_danger_button_style())
        msg.exec_()
        return msg.clickedButton() == si

    def confirmar_eliminar_libro(self, id_libro):
        if self._confirmar_eliminacion(
            tr("books.delete_confirm_title"),
            tr("books.delete_confirm"),
            tr("books.delete_irreversible"),
        ):
            self.eliminar_libro(id_libro)

    def confirmar_eliminar_coleccion(self, id_coleccion, nombre):
        if self._confirmar_eliminacion(
            tr("books.delete_confirm_title"),
            tr("collection.delete_confirm", name=nombre),
            tr("books.delete_irreversible"),
        ):
            self.eliminar_coleccion(id_coleccion)

    def eliminar_libro(self, id_libro):
        from crud import eliminar_libro
        if eliminar_libro(id_libro):
            self.cargar_pdf_desde_db()
            QMessageBox.information(
                self, tr("common.success"), tr("books.deleted")
            )
        else:
            QMessageBox.warning(
                self, tr("common.error"), tr("books.delete_failed")
            )

    def eliminar_coleccion(self, id_coleccion):
        from crud import eliminar_coleccion
        if eliminar_coleccion(id_coleccion):
            self.actualizar_lista_colecciones()
            QMessageBox.information(
                self, tr("common.success"), tr("collection.deleted")
            )
        else:
            QMessageBox.warning(
                self, tr("common.error"), tr("collection.delete_failed")
            )

    def limpiar_panel_derecho(self):
        if self.contenido_dinamico.count() > 0:
            self.contenido_dinamico.setCurrentIndex(0)

    def abrir_pdf_desde_ruta(self, ruta_pdf):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, ruta_pdf)
        item.setData(Qt.UserRole + 1, 0)
        self.abrir_pdf(item)
