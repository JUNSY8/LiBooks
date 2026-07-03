import logging
import os

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit,
    QFrame, QFileDialog, QMessageBox,
    QDialog, QScrollArea, QStackedWidget, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from crud import (
    es_duplicado, ruta_absoluta_libro, consultar_biblioteca,
    asignar_etiquetas_libro, asignar_brillo_libro,
    obtener_etiquetas,
)
from brillo import opciones_filtro_brillo
from message_boxes import show_info, show_warning, show_error, confirm
from pdf_viewer import PDFViewer
from datos import Datos
from dialogs import ColeccionDialog
from settings_dialog import SettingsDialog
from library_view import LibraryPanel
from stats_view import StatsPanel
from app_settings import (
    get_library_sort, set_library_sort,
    get_library_filter, set_library_filter,
    get_library_tag_filter, set_library_tag_filter,
    get_library_brillo_filter, set_library_brillo_filter,
)
from book_import import (
    importar_carpeta, importar_varios, metadatos_para_formulario,
    importar_pdf_con_dialogo, ImportResult,
)
from pdf_meta import recoger_pdfs_en_carpeta
from icons import app_icon, icon_label, pixmap, set_button_icon
from i18n import tr, register_language_callback
from styles import ACCENT_TEXT, TEXT_PRIMARY, TEXT_SECONDARY

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
        self._total_book_count = 0
        self._coleccion_activa = None
        register_language_callback(self.retranslate_ui)
        self.setAcceptDrops(True)
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
        from trial_manager import access_status
        status, days = access_status()
        if status == "trial":
            self._lbl_subtitle.setText(tr("app.trial_subtitle", days=days))
        self._nav_libros_lbl.setText(tr("nav.my_books"))
        self._nav_buttons["stats"].setText(tr("nav.stats"))
        set_button_icon(
            self._nav_buttons["stats"], "chart", 18, TEXT_SECONDARY, tr("nav.stats")
        )
        self._col_lbl.setText(tr("nav.collections"))
        self._btn_add_col.setToolTip(tr("nav.new_collection"))
        set_button_icon(
            self._btn_settings, "settings", 18, TEXT_SECONDARY, tr("nav.settings")
        )
        self.btn_atras.setText(tr("nav.back"))
        self.search_bar.setPlaceholderText(tr("books.search_placeholder"))
        set_button_icon(self._btn_add, "add_book", 16, ACCENT_TEXT, tr("books.add"))
        set_button_icon(
            self._btn_import_folder, "import_folder", 16, TEXT_SECONDARY, ""
        )
        self._btn_import_folder.setToolTip(tr("library.import_folder"))
        self.library.retranslate_ui()
        self._refresh_filter_combos()
        self._lbl_sort.setText(tr("library.sort_label"))
        self._lbl_filter.setText(tr("library.filter_label"))
        self._lbl_tag_filter.setText(tr("library.tag_filter_label"))
        self._lbl_brillo_filter.setText(tr("library.brillo_filter_label"))
        if hasattr(self, "_stats_panel"):
            self._stats_panel.retranslate_ui()
        filtro = self.search_bar.text().strip()
        if self._vista_actual == "libros" and (filtro or self._book_count > 0):
            self.cargar_pdf_desde_db(filtro=filtro or None)

    def mostrar_ajustes(self):
        SettingsDialog(self).exec_()

    def mostrar_estadisticas(self):
        self._coleccion_activa = None
        self._vista_actual = "stats"
        self.btn_atras.hide()
        self.contenido_dinamico.setCurrentWidget(self.pagina_stats)
        self._stats_panel.refresh()
        self._set_nav_active("stats")

    def _sort_options(self):
        return [
            ("title_asc", tr("library.sort_title_asc")),
            ("title_desc", tr("library.sort_title_desc")),
            ("author_asc", tr("library.sort_author")),
            ("date_added_desc", tr("library.sort_date_desc")),
            ("date_added_asc", tr("library.sort_date_asc")),
            ("last_read_desc", tr("library.sort_last_read")),
            ("progress_desc", tr("library.sort_progress_desc")),
            ("progress_asc", tr("library.sort_progress_asc")),
        ]

    def _filter_options(self):
        return [
            ("all", tr("library.filter_all")),
            ("unread", tr("library.filter_unread")),
            ("reading", tr("library.filter_reading")),
            ("completed", tr("library.filter_completed")),
            ("paused", tr("library.filter_paused")),
            ("abandoned", tr("library.filter_abandoned")),
        ]

    def _init_filter_combos(self):
        self._combo_sort.blockSignals(True)
        self._combo_filter.blockSignals(True)
        self._combo_tag.blockSignals(True)
        self._combo_brillo.blockSignals(True)

        self._combo_sort.clear()
        for key, label in self._sort_options():
            self._combo_sort.addItem(label, key)
        idx = self._combo_sort.findData(get_library_sort())
        self._combo_sort.setCurrentIndex(idx if idx >= 0 else 0)

        self._combo_filter.clear()
        for key, label in self._filter_options():
            self._combo_filter.addItem(label, key)
        idx = self._combo_filter.findData(get_library_filter())
        self._combo_filter.setCurrentIndex(idx if idx >= 0 else 0)

        self._refresh_filter_combos()

        self._combo_sort.blockSignals(False)
        self._combo_filter.blockSignals(False)
        self._combo_tag.blockSignals(False)
        self._combo_brillo.blockSignals(False)

    def _refresh_filter_combos(self):
        tag_id = get_library_tag_filter()
        self._combo_tag.blockSignals(True)
        self._combo_tag.clear()
        self._combo_tag.addItem(tr("library.tag_filter_all"), None)
        for et in obtener_etiquetas():
            self._combo_tag.addItem(et.nombre, et.id_etiqueta)
        idx = self._combo_tag.findData(tag_id)
        self._combo_tag.setCurrentIndex(idx if idx >= 0 else 0)
        self._combo_tag.blockSignals(False)

        brillo_val = get_library_brillo_filter()
        self._combo_brillo.blockSignals(True)
        self._combo_brillo.clear()
        for valor, etiqueta in opciones_filtro_brillo():
            self._combo_brillo.addItem(etiqueta, valor)
        idx = self._combo_brillo.findData(brillo_val)
        self._combo_brillo.setCurrentIndex(idx if idx >= 0 else 0)
        self._combo_brillo.blockSignals(False)

    def _on_library_filters_changed(self):
        set_library_sort(self._combo_sort.currentData())
        set_library_filter(self._combo_filter.currentData())
        set_library_tag_filter(self._combo_tag.currentData())
        set_library_brillo_filter(self._combo_brillo.currentData())
        if self._vista_actual == "libros":
            self.cargar_pdf_desde_db(filtro=self.search_bar.text().strip() or None)

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
        self._nav_buttons["libros"] = self._make_books_nav_item()
        sl.addWidget(self._nav_buttons["libros"])

        self._nav_buttons["stats"] = self._make_nav_btn(
            "", "stats", self.mostrar_estadisticas, "chart"
        )
        sl.addWidget(self._nav_buttons["stats"])
        sl.addSpacing(8)

        # Colecciones con botón +
        col_header = QHBoxLayout()
        col_header.setContentsMargins(8, 8, 4, 4)
        col_lbl = QLabel()
        col_lbl.setObjectName("fieldLabel")
        self._col_lbl = col_lbl
        btn_add_col = QPushButton()
        btn_add_col.setObjectName("addCollectionBtn")
        self._btn_add_col = btn_add_col
        set_button_icon(btn_add_col, "add_collection", 16)
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

    def _make_books_nav_item(self):
        row = QFrame()
        row.setObjectName("navItem")
        row.setProperty("active", False)
        row.setCursor(Qt.PointingHandCursor)

        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        self._nav_libros_icon = icon_label("books", 18, TEXT_SECONDARY)
        self._nav_libros_lbl = QLabel()
        self._nav_libros_lbl.setObjectName("navItemLabel")
        self._nav_libros_badge = QLabel("0")
        self._nav_libros_badge.setObjectName("navBadge")
        self._nav_libros_badge.setAlignment(Qt.AlignCenter)

        lay.addWidget(self._nav_libros_icon)
        lay.addWidget(self._nav_libros_lbl, 1)
        lay.addWidget(self._nav_libros_badge)

        def on_click(event):
            if event.button() == Qt.LeftButton:
                self._set_nav_active("libros")
                self.mostrar_todos_los_libros()
            QFrame.mousePressEvent(row, event)

        row.mousePressEvent = on_click
        return row

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
            active = k == key
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            if k == "libros":
                color = TEXT_PRIMARY if active else TEXT_SECONDARY
                self._nav_libros_icon.setPixmap(pixmap("books", 18, color))
            elif k == "stats" and isinstance(btn, QPushButton):
                set_button_icon(
                    btn, "chart", 18,
                    TEXT_PRIMARY if active else TEXT_SECONDARY,
                    tr("nav.stats"),
                )

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
        set_button_icon(add_btn, "add_book", 16, ACCENT_TEXT, "")
        add_btn.clicked.connect(self.agregar_libro_pdf)

        self._btn_import_folder = QPushButton()
        self._btn_import_folder.setObjectName("ghostButton")
        self._btn_import_folder.clicked.connect(self.importar_carpeta)

        header.addWidget(self.btn_atras)
        header.addWidget(self.search_bar, 1)
        header.addWidget(self._btn_import_folder)
        header.addWidget(add_btn)
        libros_layout.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(12)
        self._lbl_sort = QLabel()
        self._lbl_sort.setObjectName("fieldLabel")
        self._combo_sort = QComboBox()
        self._combo_sort.setObjectName("libraryFilterCombo")
        self._combo_sort.currentIndexChanged.connect(self._on_library_filters_changed)

        self._lbl_filter = QLabel()
        self._lbl_filter.setObjectName("fieldLabel")
        self._combo_filter = QComboBox()
        self._combo_filter.setObjectName("libraryFilterCombo")
        self._combo_filter.currentIndexChanged.connect(self._on_library_filters_changed)

        self._lbl_tag_filter = QLabel()
        self._lbl_tag_filter.setObjectName("fieldLabel")
        self._combo_tag = QComboBox()
        self._combo_tag.setObjectName("libraryFilterCombo")
        self._combo_tag.currentIndexChanged.connect(self._on_library_filters_changed)

        self._lbl_brillo_filter = QLabel()
        self._lbl_brillo_filter.setObjectName("fieldLabel")
        self._combo_brillo = QComboBox()
        self._combo_brillo.setObjectName("libraryFilterCombo")
        self._combo_brillo.currentIndexChanged.connect(self._on_library_filters_changed)

        filters.addWidget(self._lbl_sort)
        filters.addWidget(self._combo_sort)
        filters.addWidget(self._lbl_filter)
        filters.addWidget(self._combo_filter)
        filters.addWidget(self._lbl_tag_filter)
        filters.addWidget(self._combo_tag)
        filters.addWidget(self._lbl_brillo_filter)
        filters.addWidget(self._combo_brillo, 1)
        libros_layout.addLayout(filters)
        self._init_filter_combos()

        self.library = LibraryPanel()
        self.library.open_requested.connect(self._abrir_libro)
        self.library.edit_requested.connect(self.mostrar_dialogo_actualizar)
        self.library.delete_requested.connect(self.confirmar_eliminar_libro)
        self.library.tags_changed.connect(self._on_book_tags_changed)
        self.library.brillo_changed.connect(self._on_book_brillo_changed)
        self.library.files_dropped.connect(self._importar_archivos)
        libros_layout.addWidget(self.library, 1)

        self.contenido_dinamico.addWidget(self.pagina_libros)

        self.pagina_stats = StatsPanel()
        self._stats_panel = self.pagina_stats
        self.contenido_dinamico.addWidget(self.pagina_stats)

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
        self._nav_libros_badge.setText(str(self._total_book_count))

    def _mostrar_resumen_importacion(self, result: ImportResult):
        if result.added == 0 and result.duplicates == 0 and result.failed == 0:
            return
        partes = []
        if result.added:
            partes.append(tr("library.import_added", n=result.added))
        if result.duplicates:
            partes.append(tr("library.import_duplicates", n=result.duplicates))
        if result.failed:
            partes.append(tr("library.import_failed", n=result.failed))
        show_info(self, tr("library.import_title"), "\n".join(partes))

    def _importar_archivos(self, rutas):
        result = importar_varios(rutas)
        if result.added or result.duplicates or result.failed:
            self.cargar_pdf_desde_db(filtro=self.search_bar.text().strip() or None)
            self._mostrar_resumen_importacion(result)

    def importar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, tr("library.select_folder")
        )
        if not carpeta:
            return
        pdfs = recoger_pdfs_en_carpeta(carpeta)
        if not pdfs:
            show_info(self, tr("library.import_title"), tr("library.folder_empty"))
            return
        result = importar_carpeta(carpeta)
        self.cargar_pdf_desde_db(filtro=self.search_bar.text().strip() or None)
        self._mostrar_resumen_importacion(result)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            pdfs = [
                u.toLocalFile() for u in event.mimeData().urls()
                if u.toLocalFile().lower().endswith(".pdf")
            ]
            if pdfs:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            rutas = [
                u.toLocalFile() for u in event.mimeData().urls()
                if u.toLocalFile().lower().endswith(".pdf")
            ]
            if rutas:
                self._importar_archivos(rutas)
                event.acceptProposedAction()
                return
        event.ignore()

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

        existente = es_duplicado(archivo)
        if existente:
            show_info(
                self,
                tr("library.duplicate_title"),
                tr("library.duplicate_single", title=existente.titulo),
            )
            return

        try:
            titulo_sug, autor_sug = metadatos_para_formulario(archivo)
            dialogo = Datos(self, modo="añadir", archivo=archivo)
            dialogo.titulo_input.setText(titulo_sug)
            dialogo.autor_input.setText(autor_sug)

            if dialogo.exec_() == QDialog.Accepted:
                titulo, autor, genero, etiquetas, estado_manual = dialogo.obtener_datos()
                estado, libro = importar_pdf_con_dialogo(
                    archivo, titulo, autor, genero
                )
                if estado == "added" and libro:
                    if etiquetas:
                        asignar_etiquetas_libro(libro.id_libro, etiquetas)
                    asignar_brillo_libro(libro.id_libro, dialogo.obtener_brillo())
                    from crud import actualizar_libro
                    if estado_manual and estado_manual != "auto":
                        actualizar_libro(libro.id_libro, estado_manual=estado_manual)
                    self._refresh_filter_combos()
                    self.cargar_pdf_desde_db()
                    show_info(self, tr("common.success"), tr("books.added"))
                elif estado == "duplicate":
                    show_info(
                        self,
                        tr("library.duplicate_title"),
                        tr("library.duplicate_single", title=titulo),
                    )
                else:
                    show_warning(self, tr("common.error"), tr("books.add_failed"))
        except Exception as e:
            show_error(self, tr("common.error"), tr("books.add_error", error=e))

    def mostrar_dialogo_actualizar(self, id_libro):
        from crud import obtener_libro_por_id

        libro = obtener_libro_por_id(id_libro)
        if not libro:
            show_warning(self, tr("common.error"), tr("books.not_found"))
            return

        from db import PDF_FOLDER
        ruta = (
            os.path.join(PDF_FOLDER, libro.archivo_pdf)
            if libro.archivo_pdf else None
        )

        dialog = Datos(self, modo="editar", archivo=ruta, libro_id=id_libro)
        dialog.titulo_input.setText(libro.titulo)
        dialog.autor_input.setText(libro.autor.nombre if libro.autor else "")
        dialog.genero_input.setText(libro.genero.nombre if libro.genero else "")
        dialog.set_brillo_libro(libro)
        dialog.set_etiquetas_libro(libro)

        dialog.boton_guardar.clicked.disconnect()
        dialog.boton_guardar.clicked.connect(
            lambda: self.guardar_actualizacion(id_libro, dialog)
        )
        dialog.configurar_eliminar(
            lambda: (dialog.reject(), self.confirmar_eliminar_libro(id_libro))
        )
        dialog.exec_()

    def _on_book_brillo_changed(self, id_libro, nivel):
        try:
            if not asignar_brillo_libro(id_libro, nivel):
                show_error(self, tr("common.error"), tr("books.brillo_update_error"))
                return
            filtro = self.search_bar.text().strip() or None
            brillo_filtro = self._combo_brillo.currentData()
            if brillo_filtro is not None:
                visible = (
                    (brillo_filtro == 0 and not nivel)
                    or brillo_filtro == nivel
                )
                if not visible:
                    self.cargar_pdf_desde_db(filtro=filtro)
        except Exception as e:
            logger.exception("Error al actualizar brillo: %s", e)
            show_error(self, tr("common.error"), tr("books.brillo_update_error", error=e))

    def _on_book_tags_changed(self, id_libro, estado, etiquetas_libres):
        try:
            from crud import actualizar_libro
            from reading_status import construir_etiquetas_guardado

            estado_manual = None if estado == "auto" else estado
            nombres = construir_etiquetas_guardado(estado_manual, etiquetas_libres)
            asignar_etiquetas_libro(id_libro, nombres)
            actualizar_libro(id_libro, estado_manual=estado)
            self._refresh_filter_combos()
            self.cargar_pdf_desde_db(
                filtro=self.search_bar.text().strip() or None
            )
        except Exception as e:
            logger.exception("Error al actualizar etiquetas: %s", e)
            show_error(self, tr("common.error"), tr("books.tags_update_error", error=e))

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
                estado_manual=dialog.obtener_estado_manual(),
            )
            asignar_etiquetas_libro(id_libro, dialog.obtener_etiquetas())
            asignar_brillo_libro(id_libro, dialog.obtener_brillo())
            self._refresh_filter_combos()
            self.cargar_pdf_desde_db()
            show_info(self, tr("common.success"), tr("books.updated"))
            dialog.accept()
        except Exception as e:
            show_error(self, tr("common.error"), tr("books.update_error", error=e))

    # ── Libros ─────────────────────────────────────────────────────────

    def cargar_pdf_desde_db(self, filtro=None):
        try:
            self._vista_actual = "libros"
            self.contenido_dinamico.setCurrentWidget(self.pagina_libros)

            total = len(consultar_biblioteca(solo_con_archivo=True))
            self._total_book_count = total

            libros = consultar_biblioteca(
                filtro_texto=filtro,
                orden=self._combo_sort.currentData() or get_library_sort(),
                estado=self._combo_filter.currentData() or get_library_filter(),
                id_etiqueta=self._combo_tag.currentData(),
                id_coleccion=self._coleccion_activa,
                brillo=self._combo_brillo.currentData(),
            )

            show_continue = self._coleccion_activa is None
            count = self.library.load_books(libros, show_continue=show_continue)
            self._actualizar_contador(count)
        except Exception as e:
            logger.exception("Error al cargar PDFs: %s", e)
            show_error(self, tr("common.error"), tr("books.load_error", error=e))

    def _abrir_libro(self, libro_id, ruta):
        try:
            if not ruta or not os.path.exists(ruta):
                show_warning(self, tr("common.error"), tr("books.pdf_not_found"))
                return
            PDFViewer(ruta, libro_id or None).exec_()
            self.cargar_pdf_desde_db(filtro=self.search_bar.text().strip() or None)
            if hasattr(self, "_stats_panel"):
                self._stats_panel.refresh()
        except Exception as e:
            logger.exception("Error al abrir PDF: %s", e)
            show_error(self, tr("common.error"), tr("books.open_error", error=e))

    def obtener_libro(self, id_libro):
        """Devuelve metadatos ligeros de un libro (autor/género como texto)."""
        try:
            from crud import obtener_libro_por_id
            libro = obtener_libro_por_id(id_libro)
            if libro:
                return type("Libro", (object,), {
                    "id_libro": libro.id_libro,
                    "titulo": libro.titulo,
                    "autor": libro.autor.nombre if libro.autor else None,
                    "genero": libro.genero.nombre if libro.genero else None,
                    "archivo_pdf": libro.archivo_pdf,
                    "estado_manual": libro.estado_manual,
                })()
        except Exception as e:
            logger.exception("Error al obtener libro: %s", e)
        return None

    # ── Colecciones y filtros ──────────────────────────────────────────

    def mostrar_todos_los_libros(self):
        self._coleccion_activa = None
        self.btn_atras.hide()
        self.contenido_dinamico.setCurrentWidget(self.pagina_libros)
        self._set_nav_active("libros")
        self.cargar_pdf_desde_db()

    def aplicar_filtros_coleccion(self, filtros):
        if filtros.get("id_coleccion"):
            self._coleccion_activa = filtros["id_coleccion"]
            self._vista_actual = "libros"
            self.contenido_dinamico.setCurrentWidget(self.pagina_libros)
            self._set_nav_active("libros")
            self.cargar_pdf_desde_db(filtro=self.search_bar.text().strip() or None)
            self.btn_atras.show()
        else:
            from crud import obtener_libros
            libros = obtener_libros()
            if filtros.get("libro_id"):
                libros = [l for l in libros if l.id_libro == filtros["libro_id"]]
            if filtros.get("autor_id"):
                libros = [l for l in libros if l.autor and l.autor.id_autor == filtros["autor_id"]]
            if filtros.get("genero_id"):
                libros = [l for l in libros if l.genero and l.genero.id_genero == filtros["genero_id"]]
            validos = [lb for lb in libros if ruta_absoluta_libro(lb)]
            count = self.library.load_books(validos, show_continue=False)
            self._actualizar_contador(count)
            self.btn_atras.show()

    def filtrar_libros(self, texto):
        self.cargar_pdf_desde_db(filtro=texto)

    def realizar_busqueda(self):
        self.filtrar_libros(self.search_bar.text())

    # ── Confirmaciones ─────────────────────────────────────────────────

    def _confirmar_eliminacion(self, titulo, mensaje, info=""):
        return confirm(
            self,
            titulo,
            mensaje,
            informative=info,
            yes_text=tr("common.delete_yes"),
            no_text=tr("common.cancel"),
            destructive=True,
            icon=QMessageBox.Question,
        )

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
            show_info(self, tr("common.success"), tr("books.deleted"))
        else:
            show_warning(self, tr("common.error"), tr("books.delete_failed"))

    def eliminar_coleccion(self, id_coleccion):
        from crud import eliminar_coleccion
        if eliminar_coleccion(id_coleccion):
            self.actualizar_lista_colecciones()
            show_info(self, tr("common.success"), tr("collection.deleted"))
        else:
            show_warning(self, tr("common.error"), tr("collection.delete_failed"))

    def limpiar_panel_derecho(self):
        if self.contenido_dinamico.count() > 0:
            self.contenido_dinamico.setCurrentIndex(0)

    def closeEvent(self, event):
        from sync_engine import sync_if_enabled
        sync_if_enabled(push_only=True)
        super().closeEvent(event)

    def abrir_pdf_desde_ruta(self, ruta_pdf):
        self._abrir_libro(0, ruta_pdf)
