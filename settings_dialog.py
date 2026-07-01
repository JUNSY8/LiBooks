"""Diálogo de ajustes de LiBooks."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt

from i18n import tr, get_language, set_language, available_languages
from icons import app_icon, icon_label, set_button_icon
from styles import ACCENT, ACCENT_TEXT, TEXT_SECONDARY


class SettingsDialog(QDialog):
    """Modal de configuración (idioma)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        icon_box = QFrame()
        icon_box.setObjectName("dialogIconBox")
        il = QHBoxLayout(icon_box)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(icon_label("settings", 20, ACCENT))
        self._title = QLabel()
        self._title.setObjectName("dialogTitle")
        self._btn_close = QPushButton()
        self._btn_close.setObjectName("closeDialogBtn")
        self._btn_close.clicked.connect(self.reject)
        header.addWidget(icon_box)
        header.addWidget(self._title, 1)
        header.addWidget(self._btn_close)
        root.addLayout(header)

        self._lang_label = QLabel()
        self._lang_label.setObjectName("fieldLabel")
        self._lang_combo = QComboBox()
        for code, name in available_languages().items():
            self._lang_combo.addItem(name, code)
        idx = self._lang_combo.findData(get_language())
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

        self._hint = QLabel()
        self._hint.setObjectName("appSubtitle")
        self._hint.setWordWrap(True)

        root.addWidget(self._lang_label)
        root.addWidget(self._lang_combo)
        root.addWidget(self._hint)

        divider = QFrame()
        divider.setObjectName("dialogDivider")
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        footer = QHBoxLayout()
        footer.addStretch()
        self._btn_cancel = QPushButton()
        self._btn_cancel.setObjectName("secondaryButton")
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_save = QPushButton()
        self._btn_save.setObjectName("primaryButton")
        self._btn_save.clicked.connect(self._save)
        footer.addWidget(self._btn_cancel)
        footer.addWidget(self._btn_save)
        root.addLayout(footer)

    def retranslate_ui(self):
        self.setWindowTitle(tr("settings.title"))
        self._title.setText(tr("settings.title"))
        self._lang_label.setText(tr("settings.language"))
        self._hint.setText(tr("settings.language_hint"))
        self._btn_cancel.setText(tr("common.cancel"))
        set_button_icon(self._btn_save, "check", 16, ACCENT_TEXT, tr("common.save"))
        set_button_icon(self._btn_close, "close", 16, TEXT_SECONDARY)
        self._btn_close.setToolTip(tr("common.close"))

    def _save(self):
        lang = self._lang_combo.currentData()
        if lang != get_language():
            set_language(lang)
        QMessageBox.information(self, tr("settings.title"), tr("settings.saved"))
        self.accept()
