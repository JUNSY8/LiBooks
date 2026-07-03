"""Selector visual de etiquetas y estados para tarjetas de libro."""

from typing import List, Optional, Set

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QScrollArea, QSizePolicy, QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

from crud import obtener_etiquetas
from i18n import tr
from reading_status import (
    READING_STATUSES,
    etiqueta_de_estado,
    es_etiqueta_de_estado,
)

TAG_STATUS_CHIP_NAMES = {
    "unread": "tagStatusChipUnread",
    "reading": "tagStatusChipReading",
    "completed": "tagStatusChipCompleted",
    "paused": "tagStatusChipPaused",
    "abandoned": "tagStatusChipAbandoned",
}


class TagPickerPopup(QFrame):
    status_changed = pyqtSignal(object)
    custom_toggled = pyqtSignal(str, bool)
    new_tag_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("tagPickerPopup")
        self._status_buttons: List[QPushButton] = []
        self._custom_buttons: List[QPushButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("tagPickerScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(360)

        body = QWidget()
        self._body = QVBoxLayout(body)
        self._body.setContentsMargins(0, 6, 0, 6)
        self._body.setSpacing(0)
        scroll.setWidget(body)
        root.addWidget(scroll)

        footer = QFrame()
        footer.setObjectName("tagPickerFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 10)
        self._btn_new = QPushButton()
        self._btn_new.setObjectName("tagPickerNewBtn")
        self._btn_new.setCursor(Qt.PointingHandCursor)
        self._btn_new.clicked.connect(self._on_new_tag)
        footer_layout.addWidget(self._btn_new)
        root.addWidget(footer)
        self.retranslate_ui()

    def retranslate_ui(self):
        self._btn_new.setText(tr("library.tag_add_new"))

    def populate(self, estado_manual: Optional[str], custom_selected: Set[str]):
        while self._body.count():
            item = self._body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status_buttons.clear()
        self._custom_buttons.clear()

        self._add_section_header(tr("library.tag_status_section"))
        status_wrap = QWidget()
        status_layout = QVBoxLayout(status_wrap)
        status_layout.setContentsMargins(8, 2, 8, 6)
        status_layout.setSpacing(2)
        status_layout.addWidget(
            self._make_status_option(tr("reading_status.auto"), estado_manual is None, None)
        )
        for key in READING_STATUSES:
            status_layout.addWidget(
                self._make_status_option(etiqueta_de_estado(key), estado_manual == key, key)
            )
        self._body.addWidget(status_wrap)
        self._add_separator()
        self._add_section_header(tr("library.tag_custom_section"))

        custom_wrap = QWidget()
        custom_layout = QVBoxLayout(custom_wrap)
        custom_layout.setContentsMargins(8, 2, 8, 4)
        custom_layout.setSpacing(2)
        db_names = sorted(
            {e.nombre for e in obtener_etiquetas() if not es_etiqueta_de_estado(e.nombre)},
            key=str.lower,
        )
        for nombre in db_names:
            selected = nombre.lower() in {t.lower() for t in custom_selected}
            btn = self._make_custom_option(nombre, selected)
            custom_layout.addWidget(btn)
            self._custom_buttons.append(btn)
        if not db_names:
            empty = QLabel(tr("library.tag_custom_empty"))
            empty.setObjectName("tagPickerEmpty")
            empty.setAlignment(Qt.AlignCenter)
            custom_layout.addWidget(empty)
        self._body.addWidget(custom_wrap)
        self.adjustSize()

    def _add_section_header(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("tagPickerSectionHeader")
        self._body.addWidget(lbl)

    def _add_separator(self):
        line = QFrame()
        line.setObjectName("tagPickerSeparator")
        line.setFrameShape(QFrame.HLine)
        self._body.addWidget(line)

    def _make_status_option(self, text: str, checked: bool, estado_key: Optional[str]):
        btn = QPushButton(text)
        btn.setObjectName("tagPickerOption")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(36)
        btn.clicked.connect(
            lambda _checked=False, k=estado_key, b=btn: self._on_status_clicked(k, b)
        )
        self._status_buttons.append(btn)
        return btn

    def _make_custom_option(self, text: str, checked: bool):
        btn = QPushButton(text)
        btn.setObjectName("tagPickerOption")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(36)
        btn.toggled.connect(lambda on, n=text: self.custom_toggled.emit(n, on))
        return btn

    def _on_status_clicked(self, key: Optional[str], source_btn: QPushButton):
        for btn in self._status_buttons:
            if btn is not source_btn:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        source_btn.blockSignals(True)
        source_btn.setChecked(True)
        source_btn.blockSignals(False)
        self.status_changed.emit(key)
        self.close()

    def _on_new_tag(self):
        nombre, ok = QInputDialog.getText(
            self, tr("library.tag_add_new"), tr("library.tag_new_prompt")
        )
        if ok and nombre.strip() and not es_etiqueta_de_estado(nombre.strip()):
            self.new_tag_requested.emit(nombre.strip())
            self.close()

    def show_below(self, anchor: QWidget):
        self.adjustSize()
        self.move(anchor.mapToGlobal(QPoint(0, anchor.height() + 6)))
        self.show()
        self.raise_()
