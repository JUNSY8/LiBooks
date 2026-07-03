"""Diálogo de activación de licencia LiBooks."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSizePolicy,
)
from PyQt5.QtCore import Qt

from license_core import LicenseError, get_machine_id, format_license_info
from license_manager import activate_license, load_stored_license
from trial_manager import access_status
from i18n import tr
from message_boxes import wire_dialog_buttons, show_info, show_warning, show_error
from icons import app_icon, set_button_icon
from styles import app_stylesheet, ACCENT_TEXT
_STYLE = app_stylesheet()


class LicenseDialog(QDialog):
    """Solicita una clave de licencia antes de permitir el uso de la aplicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activated_payload = None
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setWindowIcon(app_icon())
        self.setStyleSheet(_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        self._title = QLabel()
        self._title.setObjectName("dialogTitle")
        layout.addWidget(self._title)

        self._subtitle = QLabel()
        self._subtitle.setObjectName("appSubtitle")
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._subtitle)

        self._key_label = QLabel()
        self._key_label.setObjectName("fieldLabel")
        layout.addWidget(self._key_label)
        self.key_input = QTextEdit()
        self.key_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.key_input.setMaximumHeight(90)
        stored = load_stored_license()
        if stored:
            self.key_input.setPlainText(stored)
        layout.addWidget(self.key_input)

        self._machine_label = QLabel()
        self._machine_label.setObjectName("appSubtitle")
        self._machine_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._machine_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton()
        self._cancel_btn.setObjectName("secondaryButton")
        self._cancel_btn.clicked.connect(self.reject)
        self._activate_btn = QPushButton()
        self._activate_btn.setObjectName("primaryButton")
        self._activate_btn.clicked.connect(self._on_activate)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._activate_btn)
        layout.addLayout(btn_row)

        wire_dialog_buttons(self._cancel_btn, self._activate_btn)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("license.window_title"))
        self._title.setText(tr("license.title"))
        self._subtitle.setText(tr("license.subtitle"))
        status, days = access_status()
        if status == "trial":
            self._subtitle.setText(tr("license.subtitle_trial", days=days))
        elif status == "expired":
            self._subtitle.setText(tr("license.subtitle_expired"))
        self._key_label.setText(tr("license.key_label"))
        self.key_input.setPlaceholderText(tr("license.key_placeholder"))
        self._machine_label.setText(
            tr("license.machine_id", machine_id=get_machine_id())
        )
        self._cancel_btn.setText(tr("license.exit"))
        set_button_icon(
            self._activate_btn, "check", 16, ACCENT_TEXT, tr("license.activate")
        )

    def _on_activate(self):
        key = self.key_input.toPlainText().strip()
        if not key:
            show_warning(self, tr("license.title"), tr("license.enter_key"))
            return
        try:
            payload = activate_license(key)
            self.activated_payload = payload
            show_info(
                self,
                tr("license.activated_title"),
                tr("license.activated", info=format_license_info(payload)),
            )
            self.accept()
        except LicenseError as e:
            show_error(
                self,
                tr("license.invalid_title"),
                tr("license.invalid_support", error=str(e)),
            )


def prompt_for_license(parent=None) -> bool:
    """Muestra el diálogo de activación. Devuelve True si la licencia es válida."""
    dialog = LicenseDialog(parent)
    return dialog.exec_() == QDialog.Accepted
