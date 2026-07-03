"""Visor PDF LiBooks — lectura, búsqueda, resaltados y anotaciones."""

import logging

import fitz
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTextEdit, QScrollArea, QWidget, QFrame,
    QSplitter, QSizePolicy,
)
from PyQt5.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt5.QtGui import QImage, QPixmap, QKeySequence

from crud import (
    actualizar_paginas_leidas, obtener_paginas_leidas,
    crear_nota, crear_resaltado,
)
from pdf_page import PageWidget
from pdf_sidebar import AnnotationsPanel
from pdf_ocr import OcrManager, is_tesseract_available, guardar_pdf_buscable
from ocr_worker import start_ocr_thread
from icons import set_button_icon
from i18n import tr
from message_boxes import show_info, show_warning, show_error, confirm, wire_dialog_buttons
from styles import (
    notes_dialog_stylesheet,
    pdf_viewer_stylesheet,
    ACCENT_TEXT,
    TEXT_SECONDARY,
)

logger = logging.getLogger(__name__)


def _form_dialog(parent, title, min_width=500):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(min_width)
    dialog.setStyleSheet(notes_dialog_stylesheet())
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    return dialog, layout


def _form_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    return lbl


def _form_field(layout, label_text, widget):
    layout.addWidget(_form_label(label_text))
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout.addWidget(widget)
    return widget


def _form_text_area(layout, label_text, widget):
    layout.addWidget(_form_label(label_text))
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout.addWidget(widget)
    return widget


def _form_actions(layout, dialog, save_text=None):
    btn_layout = QHBoxLayout()
    cancel_btn = QPushButton(tr("common.cancel"))
    cancel_btn.clicked.connect(dialog.reject)
    save_btn = QPushButton(save_text or tr("common.save"))
    save_btn.clicked.connect(dialog.accept)
    btn_layout.addStretch()
    btn_layout.addWidget(cancel_btn)
    btn_layout.addWidget(save_btn)
    layout.addLayout(btn_layout)
    wire_dialog_buttons(cancel_btn, save_btn)


class SelectionPopup(QFrame):
    """Acciones rápidas tras seleccionar texto."""

    def __init__(self, viewer, page, text, rects_json, pos: QPoint):
        super().__init__(viewer, Qt.Popup | Qt.FramelessWindowHint)
        self.viewer = viewer
        self.page = page
        self.text = text
        self.rects_json = rects_json
        self.setObjectName("selectionPopup")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)
        btn_hl = QPushButton()
        btn_hl.setObjectName("secondaryButton")
        btn_hl.clicked.connect(self._highlight)
        btn_note = QPushButton()
        btn_note.setObjectName("primaryButton")
        btn_note.clicked.connect(self._note)
        set_button_icon(btn_hl, "highlight", 16, None, tr("pdf.highlight"))
        set_button_icon(btn_note, "check", 16, ACCENT_TEXT, tr("pdf.note_from_selection"))
        lay.addWidget(btn_hl)
        lay.addWidget(btn_note)
        self.adjustSize()
        self.move(pos)

    def _highlight(self):
        self.viewer.add_highlight(self.page, self.text, self.rects_json)
        self.close()

    def _note(self):
        self.viewer.add_note_from_selection(self.page, self.text, self.rects_json)
        self.close()


class PDFViewer(QDialog):
    RENDER_BUFFER = 1

    def __init__(self, pdf_path, libro_id=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.libro_id = libro_id
        self.zoom_level = 1.0
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.page_widgets = []
        self.page_sizes = []
        self.rendered_pages = set()
        self._reading_mode = False
        self._sidebar_visible = bool(libro_id)
        self._search_matches = []
        self._search_index = -1
        self._selection_popup = None
        self._highlight_mode = False
        self._ocr = None
        self._ocr_thread = None

        self.save_timer = QTimer()
        self.save_timer.setInterval(1000)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_reading_progress)

        self.render_timer = QTimer()
        self.render_timer.setInterval(60)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render_visible_pages)

        self.setObjectName("pdfViewer")
        self.setWindowTitle(tr("pdf.viewer_title"))
        self.setGeometry(100, 100, 1100, 820)
        self.setStyleSheet(pdf_viewer_stylesheet())
        self.setFocusPolicy(Qt.StrongFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._toolbar = QFrame()
        self._toolbar.setObjectName("viewerToolbar")
        tb = QHBoxLayout(self._toolbar)
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(8)

        self._nav_prev = QPushButton()
        self._nav_prev.setObjectName("viewerTextBtn")
        self._nav_prev.clicked.connect(self._prev_page)

        self.page_indicator = QLabel()
        self.page_indicator.setObjectName("viewerToolbarLabel")

        self._nav_next = QPushButton()
        self._nav_next.setObjectName("viewerTextBtn")
        self._nav_next.clicked.connect(self._next_page)

        tb.addWidget(self._nav_prev)
        tb.addWidget(self.page_indicator)
        tb.addWidget(self._nav_next)
        tb.addSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("viewerSearch")
        self.search_input.returnPressed.connect(self._run_search)
        self.search_input.textChanged.connect(self._on_search_text_changed)

        self._btn_search = QPushButton()
        self._btn_search.setObjectName("viewerTextBtn")
        self._btn_search.clicked.connect(self._run_search)

        self._search_status = QLabel()
        self._search_status.setObjectName("viewerSearchCount")

        self._btn_search_prev = QPushButton()
        self._btn_search_prev.setObjectName("viewerTextBtn")
        self._btn_search_prev.clicked.connect(self._search_prev)

        self._btn_search_next = QPushButton()
        self._btn_search_next.setObjectName("viewerTextBtn")
        self._btn_search_next.clicked.connect(self._search_next)

        tb.addWidget(self.search_input, 1)
        tb.addWidget(self._btn_search)
        tb.addWidget(self._search_status)
        tb.addWidget(self._btn_search_prev)
        tb.addWidget(self._btn_search_next)
        tb.addSpacing(12)

        self._btn_highlight = QPushButton()
        self._btn_highlight.setObjectName("viewerTextBtn")
        self._btn_highlight.setCheckable(True)
        self._btn_highlight.toggled.connect(self._on_highlight_mode)

        self._btn_reading = QPushButton()
        self._btn_reading.setObjectName("viewerTextBtn")
        self._btn_reading.setCheckable(True)
        self._btn_reading.toggled.connect(self._set_reading_mode)

        self._btn_sidebar = QPushButton()
        self._btn_sidebar.setObjectName("viewerTextBtn")
        self._btn_sidebar.clicked.connect(self._toggle_sidebar)
        self._btn_sidebar.setEnabled(bool(libro_id))

        self._btn_fullscreen = QPushButton()
        self._btn_fullscreen.setObjectName("viewerTextBtn")
        self._btn_fullscreen.clicked.connect(self.toggle_fullscreen)

        tb.addWidget(self._btn_highlight)
        tb.addWidget(self._btn_reading)
        tb.addWidget(self._btn_sidebar)
        tb.addWidget(self._btn_fullscreen)
        root.addWidget(self._toolbar)

        self._ocr_banner = QFrame()
        self._ocr_banner.setObjectName("ocrBanner")
        self._ocr_banner.hide()
        ocr_lay = QHBoxLayout(self._ocr_banner)
        ocr_lay.setContentsMargins(12, 8, 12, 8)
        self._ocr_label = QLabel()
        self._ocr_label.setObjectName("ocrBannerText")
        self._ocr_label.setWordWrap(True)
        self._btn_ocr_enable = QPushButton()
        self._btn_ocr_enable.setObjectName("secondaryButton")
        self._btn_ocr_enable.clicked.connect(self._start_ocr)
        self._btn_ocr_save = QPushButton()
        self._btn_ocr_save.setObjectName("ghostButton")
        self._btn_ocr_save.clicked.connect(self._save_searchable_pdf)
        self._ocr_progress = QLabel()
        self._ocr_progress.setObjectName("ocrBannerProgress")
        ocr_lay.addWidget(self._ocr_label, 1)
        ocr_lay.addWidget(self._ocr_progress)
        ocr_lay.addWidget(self._btn_ocr_enable)
        ocr_lay.addWidget(self._btn_ocr_save)
        root.addWidget(self._ocr_banner)

        self._reading_hint = QLabel(tr("pdf.reading_mode_hint"))
        self._reading_hint.setObjectName("readingModeHint")
        self._reading_hint.setAlignment(Qt.AlignCenter)
        self._reading_hint.hide()
        root.addWidget(self._reading_hint)

        self._splitter = QSplitter(Qt.Horizontal)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("viewerScroll")
        self.scroll_area.setWidgetResizable(True)
        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.setSpacing(8)
        self.page_layout.setAlignment(Qt.AlignHCenter)
        self.scroll_area.setWidget(self.page_container)
        self._splitter.addWidget(self.scroll_area)

        self._sidebar = None
        if libro_id:
            self._sidebar = AnnotationsPanel(self)
            self._sidebar.goto_page.connect(self.scroll_to_page)
            self._sidebar.add_note_requested.connect(self._add_note_dialog)
            self._sidebar.refresh_highlights.connect(self._refresh_all_highlights)
            self._splitter.addWidget(self._sidebar)

        self._splitter.setStretchFactor(0, 1)
        root.addWidget(self._splitter, 1)

        self.scroll_area.viewport().installEventFilter(self)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

        self.retranslate_ui()

        if self.load_pdf():
            QTimer.singleShot(0, self.render_visible_pages)
            if self.libro_id:
                self.restore_reading_progress()
        if not self._sidebar_visible and self._sidebar:
            self._sidebar.hide()

    def retranslate_ui(self):
        self.page_indicator.setText(
            tr("pdf.page_indicator", current=max(self.current_page, 0) + 1,
                total=max(self.total_pages, 1))
        )
        self.search_input.setPlaceholderText(tr("pdf.search_placeholder"))
        self._nav_prev.setText(tr("pdf.prev_page_short"))
        self._nav_next.setText(tr("pdf.next_page_short"))
        self._btn_search.setText(tr("pdf.search_btn"))
        self._btn_search_prev.setText(tr("pdf.search_prev_short"))
        self._btn_search_next.setText(tr("pdf.search_next_short"))
        self._btn_highlight.setText(tr("pdf.highlight_mode"))
        self._btn_reading.setText(tr("pdf.reading_mode_btn"))
        self._btn_sidebar.setText(tr("pdf.panel_btn"))
        self._btn_fullscreen.setText(tr("pdf.fullscreen_btn"))
        self._reading_hint.setText(tr("pdf.reading_mode_hint"))
        self._ocr_label.setText(tr("ocr.banner"))
        self._btn_ocr_enable.setText(tr("ocr.enable_btn"))
        self._btn_ocr_save.setText(tr("ocr.save_searchable_btn"))
        if self._sidebar:
            self._sidebar.retranslate_ui()

    def _on_search_text_changed(self, text):
        if not text.strip():
            self._search_matches = []
            self._search_index = -1
            self._update_search_status()
            self._apply_search_highlights()

    def _update_search_status(self):
        if self._search_matches and self._search_index >= 0:
            self._search_status.setText(
                tr("pdf.search_count", current=self._search_index + 1,
                   total=len(self._search_matches))
            )
        else:
            self._search_status.setText("")

    def _on_highlight_mode(self, enabled):
        self._highlight_mode = enabled
        self._btn_highlight.setProperty("active", enabled)
        self._btn_highlight.style().unpolish(self._btn_highlight)
        self._btn_highlight.style().polish(self._btn_highlight)

    def prompt_bookmark_name(self, pagina, default=""):
        """Pide nombre opcional para un marcador."""
        dialog, form = _form_dialog(self, tr("pdf.bookmark_add_title"), min_width=400)
        form.addWidget(QLabel(tr("pdf.bookmark_page_info", page=pagina + 1)))
        name_input = QLineEdit()
        name_input.setText(default)
        name_input.setPlaceholderText(tr("pdf.bookmark_name_placeholder"))
        _form_field(form, tr("pdf.bookmark_name_label"), name_input)
        _form_actions(form, dialog)
        if dialog.exec_() != QDialog.Accepted:
            return None
        return name_input.text().strip()

    # ── Carga y renderizado ────────────────────────────────────────────

    def load_pdf(self):
        import os

        if not os.path.exists(self.pdf_path):
            show_warning(self, tr("common.error"),
                     tr("pdf.file_not_found", path=self.pdf_path))
            return False
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            logger.exception("Error al abrir PDF: %s", e)
            show_error(self, tr("common.error"), tr("pdf.open_failed"))
            return False

        self.total_pages = self.doc.page_count
        if self.total_pages == 0:
            show_warning(self, tr("common.error"), tr("pdf.empty"))
            return False

        self._construir_placeholders()
        self.page_indicator.setText(
            tr("pdf.page_indicator", current=1, total=self.total_pages)
        )
        self._init_ocr()
        return True

    def _init_ocr(self):
        from crud import obtener_libro_por_id
        file_hash = None
        if self.libro_id:
            libro = obtener_libro_por_id(self.libro_id)
            file_hash = libro.file_hash if libro else None
        self._ocr = OcrManager(self.doc, self.pdf_path, file_hash)
        if not self._ocr.needs_ocr():
            self._ocr_banner.hide()
            return
        if not is_tesseract_available():
            self._ocr_label.setText(tr("ocr.tesseract_missing"))
            self._btn_ocr_enable.hide()
            self._btn_ocr_save.hide()
            self._ocr_banner.show()
            return
        done, total = self._ocr.progress_cached()
        if done >= total and total > 0:
            self._ocr.enable()
            self._ocr_banner.hide()
            return
        if done > 0:
            self._ocr.enable()
            self._ocr_progress.setText(tr("ocr.cached_progress", done=done, total=total))
        self._ocr_banner.show()

    def _construir_placeholders(self):
        self._limpiar_layout()
        self.page_widgets = []
        self.page_sizes = []
        self.rendered_pages = set()

        for page_num in range(self.total_pages):
            rect = self.doc.load_page(page_num).rect
            self.page_sizes.append((rect.width, rect.height))
            widget = PageWidget(self, page_num)
            widget.setFixedSize(
                int(rect.width * self.zoom_level),
                int(rect.height * self.zoom_level),
            )
            widget.text_selected.connect(self._on_text_selected)
            widget.load_highlights_from_db()
            self.page_layout.addWidget(widget)
            self.page_widgets.append(widget)

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
            self.page_widgets[page_num].set_pixmap(QPixmap.fromImage(img))
            self.rendered_pages.add(page_num)
        except Exception as e:
            logger.exception("Error al renderizar página %s: %s", page_num, e)

    def _unrender_page(self, page_num):
        if page_num not in self.rendered_pages:
            return
        w, h = self.page_sizes[page_num]
        self.page_widgets[page_num].set_pixmap(None)
        self.page_widgets[page_num].setFixedSize(
            int(w * self.zoom_level), int(h * self.zoom_level)
        )
        self.rendered_pages.discard(page_num)

    def _rango_visible(self):
        if not self.page_widgets:
            return (0, -1)
        top = self.scroll_area.verticalScrollBar().value()
        bottom = top + self.scroll_area.viewport().height()
        primera, ultima = None, None
        for i, widget in enumerate(self.page_widgets):
            y = widget.y()
            if y + widget.height() >= top and y <= bottom:
                if primera is None:
                    primera = i
                ultima = i
        if primera is None:
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
        for page_num in list(self.rendered_pages):
            if page_num not in deseadas:
                self._unrender_page(page_num)
        self._apply_search_highlights()

    def _refresh_all_highlights(self):
        for w in self.page_widgets:
            w.load_highlights_from_db()
            w.update()

    def _start_ocr(self):
        if not self._ocr or not self.doc:
            return
        if self._ocr_thread:
            return
        self._btn_ocr_enable.setEnabled(False)
        self._ocr_progress.setText(tr("ocr.running"))

        def on_progress(done, total):
            self._ocr_progress.setText(tr("ocr.running_progress", done=done, total=total))

        def on_done(ok):
            self._ocr_thread = None
            self._btn_ocr_enable.setEnabled(True)
            if ok:
                self._ocr_banner.hide()
            else:
                self._ocr_progress.setText(tr("ocr.failed"))

        self._ocr_thread = start_ocr_thread(
            self._ocr, 0, self.total_pages - 1, self,
            {"progress": on_progress, "done": on_done,
             "error": lambda e: logger.error("OCR: %s", e)},
        )

    def _save_searchable_pdf(self):
        from PyQt5.QtWidgets import QFileDialog
        dest, _ = QFileDialog.getSaveFileName(
            self, tr("ocr.save_dialog_title"),
            "", tr("books.pdf_filter"),
        )
        if not dest:
            return
        if not dest.lower().endswith(".pdf"):
            dest += ".pdf"
        self._btn_ocr_save.setEnabled(False)
        self._ocr_progress.setText(tr("ocr.saving"))

        def progress(done, total):
            self._ocr_progress.setText(tr("ocr.running_progress", done=done, total=total))

        ok = guardar_pdf_buscable(self.pdf_path, dest, progress=progress)
        self._btn_ocr_save.setEnabled(True)
        if ok:
            show_info(self, tr("common.success"), tr("ocr.saved", path=dest))
        else:
            show_warning(self, tr("common.error"), tr("ocr.save_failed"))

    # ── Búsqueda ───────────────────────────────────────────────────────

    def _run_search(self):
        query = self.search_input.text().strip()
        self._search_matches = []
        self._search_index = -1
        if not query or not self.doc:
            self._update_search_status()
            self._apply_search_highlights()
            return
        if self._ocr and self._ocr.needs_ocr() and not self._ocr.active:
            show_info(self, tr("ocr.search_needs_ocr_title"), tr("ocr.search_needs_ocr"))
            return
        if self._ocr and self._ocr.active:
            self._search_matches = self._ocr.search(query)
        else:
            flags = getattr(fitz, "TEXT_IGNORECASE", 1)
            for i in range(self.total_pages):
                for rect in self.doc.load_page(i).search_for(query, flags=flags):
                    self._search_matches.append((i, rect))
        if self._search_matches:
            self._search_index = 0
            self._go_to_search_match()
        else:
            self._update_search_status()
            self._apply_search_highlights()
            show_info(self, tr("pdf.search_title"), tr("pdf.search_no_results"))

    def _search_next(self):
        if not self._search_matches:
            self._run_search()
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._go_to_search_match()

    def _search_prev(self):
        if not self._search_matches:
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._go_to_search_match()

    def _go_to_search_match(self):
        if self._search_index < 0 or not self._search_matches:
            return
        page, rect = self._search_matches[self._search_index]
        self.scroll_to_page(page)
        self._update_search_status()
        self._apply_search_highlights()
        QTimer.singleShot(80, lambda: self._scroll_to_rect(page, rect))

    def _scroll_to_rect(self, page_num, rect):
        if page_num >= len(self.page_widgets):
            return
        widget = self.page_widgets[page_num]
        y_target = widget.y() + int(rect.y0 * self.zoom_level)
        y_target -= self.scroll_area.viewport().height() // 3
        self.scroll_area.verticalScrollBar().setValue(max(0, y_target))

    def _apply_search_highlights(self):
        hits_by_page = {i: [] for i in range(self.total_pages)}
        active_coords = None
        if 0 <= self._search_index < len(self._search_matches):
            ap, ar = self._search_matches[self._search_index]
            active_coords = [ar.x0, ar.y0, ar.x1, ar.y1]
        for page, rect in self._search_matches:
            hits_by_page[page].append([rect.x0, rect.y0, rect.x1, rect.y1])
        for i, widget in enumerate(self.page_widgets):
            page_active = active_coords if (
                0 <= self._search_index < len(self._search_matches)
                and self._search_matches[self._search_index][0] == i
            ) else None
            widget.set_search_hits(hits_by_page.get(i, []), active=page_active)

    # ── Selección y anotaciones ────────────────────────────────────────

    def _on_text_selected(self, page, text, rects_json):
        if self._highlight_mode:
            self.add_highlight(page, text, rects_json)
            return
        if self._selection_popup:
            self._selection_popup.close()
        global_pos = self.mapToGlobal(self.cursor().pos())
        self._selection_popup = SelectionPopup(
            self, page, text, rects_json, global_pos
        )
        self._selection_popup.show()

    def add_highlight(self, page, text, rects_json):
        if not self.libro_id:
            return
        if crear_resaltado(self.libro_id, page, text, rects_json):
            self.page_widgets[page].load_highlights_from_db()
            if self._sidebar:
                self._sidebar.reload()

    def add_note_from_selection(self, page, text, rects_json):
        titulo = text[:50] + ("…" if len(text) > 50 else "")
        self._note_form(titulo, text, page, text, rects_json)

    def _add_note_dialog(self):
        self._note_form("", "", None, None, None)

    def _note_form(self, titulo_default, fragmento, pagina, fragmento_full, rects):
        dialog, layout = _form_dialog(self, tr("pdf.new_note_title"))
        titulo_edit = QLineEdit(titulo_default)
        titulo_edit.setPlaceholderText(tr("pdf.note_title_placeholder"))
        _form_field(layout, tr("pdf.note_title_label"), titulo_edit)
        if fragmento:
            frag_lbl = QLabel(tr("pdf.selected_text", text=fragmento))
            frag_lbl.setWordWrap(True)
            frag_lbl.setObjectName("fieldLabel")
            layout.addWidget(frag_lbl)
        contenido_edit = QTextEdit()
        contenido_edit.setPlaceholderText(tr("pdf.note_content_placeholder"))
        contenido_edit.setMinimumHeight(160)
        _form_text_area(layout, tr("pdf.note_content_label"), contenido_edit)
        _form_actions(layout, dialog)
        if dialog.exec_() != QDialog.Accepted:
            return
        titulo = titulo_edit.text().strip()
        if not titulo:
            show_warning(self, tr("common.error"),
                     tr("pdf.note_title_empty"))
            return
        try:
            crear_nota(
                titulo, self.libro_id, contenido_edit.toPlainText().strip(),
                pagina=pagina, fragmento=fragmento_full, rects=rects,
            )
            if self._sidebar:
                self._sidebar.reload()
        except Exception as e:
            logger.exception("Error al crear nota: %s", e)
            show_error(self, tr("common.error"), tr("pdf.note_create_error", error=str(e)))

    # ── Navegación y zoom ──────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                self.zoom_level = min(5.0, self.zoom_level * 1.2) if delta > 0 else max(0.2, self.zoom_level / 1.2)
                self._aplicar_zoom()
                return True
        return super().eventFilter(obj, event)

    def _aplicar_zoom(self):
        for i, widget in enumerate(self.page_widgets):
            w, h = self.page_sizes[i]
            widget.set_pixmap(None)
            widget.setFixedSize(int(w * self.zoom_level), int(h * self.zoom_level))
        self.rendered_pages = set()
        self.render_visible_pages()

    def on_scroll(self):
        if not self.doc:
            return
        primera, _ = self._rango_visible()
        if primera is not None and primera != self.current_page:
            self.current_page = primera
            self.page_indicator.setText(
                tr("pdf.page_indicator", current=primera + 1, total=self.total_pages)
            )
            if self.libro_id:
                self.save_timer.start()
        self.render_timer.start()

    def _prev_page(self):
        if self.current_page > 0:
            self.scroll_to_page(self.current_page - 1)

    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self.scroll_to_page(self.current_page + 1)

    def scroll_to_page(self, page_num):
        if 0 <= page_num < len(self.page_widgets):
            self._render_page(page_num)
            self.scroll_area.ensureWidgetVisible(self.page_widgets[page_num])
            self.current_page = page_num
            self.page_indicator.setText(
                tr("pdf.page_indicator", current=page_num + 1, total=self.total_pages)
            )
            self.render_timer.start()

    def _set_reading_mode(self, enabled):
        self._reading_mode = enabled
        self._toolbar.setVisible(not enabled)
        self._reading_hint.setVisible(enabled)
        self._btn_reading.setProperty("active", enabled)
        self._btn_reading.style().unpolish(self._btn_reading)
        self._btn_reading.style().polish(self._btn_reading)
        if enabled and self._sidebar:
            self._sidebar.hide()
            self._sidebar_visible = False
            self._btn_sidebar.setProperty("active", False)
            self._btn_sidebar.style().unpolish(self._btn_sidebar)
            self._btn_sidebar.style().polish(self._btn_sidebar)

    def _toggle_sidebar(self):
        if not self._sidebar:
            return
        self._sidebar_visible = not self._sidebar_visible
        self._sidebar.setVisible(self._sidebar_visible)
        self._btn_sidebar.setProperty("active", self._sidebar_visible)
        self._btn_sidebar.style().unpolish(self._btn_sidebar)
        self._btn_sidebar.style().polish(self._btn_sidebar)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_PageUp):
            self._prev_page()
        elif key in (Qt.Key_Right, Qt.Key_PageDown, Qt.Key_Space):
            self._next_page()
        elif key == Qt.Key_F11:
            self.toggle_fullscreen()
        elif key == Qt.Key_Escape and self._reading_mode:
            self._btn_reading.setChecked(False)
        elif key == Qt.Key_R:
            self._btn_reading.setChecked(not self._reading_mode)
        elif event.matches(QKeySequence.Find):
            self.search_input.setFocus()
            self.search_input.selectAll()
        elif key == Qt.Key_F3:
            self._search_next() if not (event.modifiers() & Qt.ShiftModifier) else self._search_prev()
        else:
            super().keyPressEvent(event)

    # ── Progreso ───────────────────────────────────────────────────────

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
