"""Diálogo de ajustes de LiBooks."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QSizePolicy, QLineEdit,
    QFileDialog, QCheckBox, QScrollArea, QWidget,
)
from PyQt5.QtCore import Qt

from i18n import tr, get_language, set_language, available_languages
from icons import app_icon, icon_label, set_button_icon
from styles import ACCENT, ACCENT_TEXT, TEXT_SECONDARY
from app_settings import (
    get_sync_enabled, get_sync_folder,
    clear_sync_secrets,
)
from sync_engine import (
    setup_sync, check_passphrase, sync_now, is_sync_configured,
    set_session_passphrase, export_to_file, import_from_file,
    SyncError,
)
from message_boxes import wire_dialog_buttons, disable_button_default, show_info, show_warning, show_error, confirm
from trial_manager import access_status
from license_manager import license_summary, get_active_license_info
from library_backup import export_backup, import_backup
from update_checker import check_for_updates
from version import APP_VERSION


class SettingsDialog(QDialog):
    """Modal de configuración (idioma + sincronización)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        root = QVBoxLayout(body)
        root.setContentsMargins(24, 20, 24, 12)
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
        self._lang_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        self._license_status = QLabel()
        self._license_status.setObjectName("appSubtitle")
        self._license_status.setWordWrap(True)
        root.addWidget(self._license_status)

        self._btn_activate = QPushButton()
        self._btn_activate.setObjectName("secondaryButton")
        self._btn_activate.clicked.connect(self._open_license)
        root.addWidget(self._btn_activate)

        div0 = QFrame()
        div0.setObjectName("dialogDivider")
        div0.setFrameShape(QFrame.HLine)
        root.addWidget(div0)

        self._backup_title = QLabel()
        self._backup_title.setObjectName("dialogTitle")
        root.addWidget(self._backup_title)
        self._backup_hint = QLabel()
        self._backup_hint.setObjectName("appSubtitle")
        self._backup_hint.setWordWrap(True)
        root.addWidget(self._backup_hint)
        backup_btns = QHBoxLayout()
        self._btn_lib_export = QPushButton()
        self._btn_lib_export.setObjectName("secondaryButton")
        self._btn_lib_export.clicked.connect(self._export_library)
        self._btn_lib_import = QPushButton()
        self._btn_lib_import.setObjectName("ghostButton")
        self._btn_lib_import.clicked.connect(self._import_library)
        backup_btns.addWidget(self._btn_lib_export)
        backup_btns.addWidget(self._btn_lib_import)
        root.addLayout(backup_btns)

        div_upd = QFrame()
        div_upd.setObjectName("dialogDivider")
        div_upd.setFrameShape(QFrame.HLine)
        root.addWidget(div_upd)

        self._update_title = QLabel()
        self._update_title.setObjectName("dialogTitle")
        root.addWidget(self._update_title)
        self._version_lbl = QLabel()
        self._version_lbl.setObjectName("appSubtitle")
        root.addWidget(self._version_lbl)
        self._btn_check_update = QPushButton()
        self._btn_check_update.setObjectName("ghostButton")
        self._btn_check_update.clicked.connect(self._check_updates)
        root.addWidget(self._btn_check_update)

        div1 = QFrame()
        div1.setObjectName("dialogDivider")
        div1.setFrameShape(QFrame.HLine)
        root.addWidget(div1)

        self._sync_title = QLabel()
        self._sync_title.setObjectName("dialogTitle")
        root.addWidget(self._sync_title)

        self._sync_hint = QLabel()
        self._sync_hint.setObjectName("appSubtitle")
        self._sync_hint.setWordWrap(True)
        root.addWidget(self._sync_hint)

        self._sync_enabled = QCheckBox()
        root.addWidget(self._sync_enabled)
        self._sync_enabled.setChecked(get_sync_enabled())

        folder_row = QHBoxLayout()
        self._sync_folder = QLineEdit()
        self._sync_folder.setReadOnly(True)
        self._sync_folder.setText(get_sync_folder() or "")
        self._btn_folder = QPushButton()
        self._btn_folder.setObjectName("secondaryButton")
        self._btn_folder.clicked.connect(self._pick_folder)
        folder_row.addWidget(self._sync_folder, 1)
        folder_row.addWidget(self._btn_folder)
        root.addLayout(folder_row)

        self._pass_label = QLabel()
        self._pass_label.setObjectName("fieldLabel")
        self._pass_input = QLineEdit()
        self._pass_input.setEchoMode(QLineEdit.Password)
        root.addWidget(self._pass_label)
        root.addWidget(self._pass_input)

        sync_btns = QHBoxLayout()
        self._btn_sync_now = QPushButton()
        self._btn_sync_now.setObjectName("secondaryButton")
        self._btn_sync_now.clicked.connect(self._do_sync)
        self._btn_sync_export = QPushButton()
        self._btn_sync_export.setObjectName("ghostButton")
        self._btn_sync_export.clicked.connect(self._export_sync_backup)
        self._btn_sync_import = QPushButton()
        self._btn_sync_import.setObjectName("ghostButton")
        self._btn_sync_import.clicked.connect(self._import_sync_backup)
        sync_btns.addWidget(self._btn_sync_now)
        sync_btns.addWidget(self._btn_sync_export)
        sync_btns.addWidget(self._btn_sync_import)
        root.addLayout(sync_btns)

        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(24, 0, 24, 20)
        footer.addStretch()
        self._btn_cancel = QPushButton()
        self._btn_cancel.setObjectName("secondaryButton")
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_save = QPushButton()
        self._btn_save.setObjectName("primaryButton")
        self._btn_save.clicked.connect(self._save)
        footer.addWidget(self._btn_cancel)
        footer.addWidget(self._btn_save)
        outer.addLayout(footer)

        wire_dialog_buttons(self._btn_cancel, self._btn_save)
        disable_button_default(self._btn_close)

    def retranslate_ui(self):
        self.setWindowTitle(tr("settings.title"))
        self._title.setText(tr("settings.title"))
        self._lang_label.setText(tr("settings.language"))
        self._hint.setText(tr("settings.language_hint"))
        self._refresh_license_status()
        self._btn_activate.setText(tr("settings.manage_license"))
        self._backup_title.setText(tr("backup.title"))
        self._backup_hint.setText(tr("backup.hint"))
        self._btn_lib_export.setText(tr("backup.export_btn"))
        self._btn_lib_import.setText(tr("backup.import_btn"))
        self._update_title.setText(tr("update.title"))
        self._version_lbl.setText(tr("update.current_version", version=APP_VERSION))
        self._btn_check_update.setText(tr("update.check_btn"))
        self._sync_title.setText(tr("sync.title"))
        self._sync_hint.setText(tr("sync.hint"))
        self._sync_enabled.setText(tr("sync.enabled"))
        self._pass_label.setText(tr("sync.passphrase_label"))
        self._pass_input.setPlaceholderText(tr("sync.passphrase_placeholder"))
        self._btn_folder.setText(tr("sync.choose_folder"))
        self._btn_sync_now.setText(tr("sync.now_btn"))
        self._btn_sync_export.setText(tr("sync.export_btn"))
        self._btn_sync_import.setText(tr("sync.import_btn"))
        self._btn_cancel.setText(tr("common.cancel"))
        set_button_icon(self._btn_save, "check", 16, ACCENT_TEXT, tr("common.save"))
        set_button_icon(self._btn_close, "close", 16, TEXT_SECONDARY)
        self._btn_close.setToolTip(tr("common.close"))

    def _refresh_license_status(self):
        status, days = access_status()
        if status == "licensed":
            self._license_status.setText(license_summary())
            self._btn_activate.setText(tr("settings.manage_license"))
        elif status == "trial":
            self._license_status.setText(tr("trial.status_active", days=days))
            self._btn_activate.setText(tr("trial.activate_btn"))
        else:
            self._license_status.setText(tr("trial.status_expired"))
            self._btn_activate.setText(tr("trial.activate_btn"))

    def _open_license(self):
        from license_dialog import prompt_for_license
        if prompt_for_license(self):
            self._refresh_license_status()

    def _export_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("backup.export_btn"), "libooks-library.zip", tr("backup.file_filter")
        )
        if not path:
            return
        try:
            stats = export_backup(path, include_pdfs=True)
            show_info(
                self, tr("common.success"),
                tr("backup.exported", path=path, books=stats["books"], pdfs=stats["pdfs"]),
            )
        except Exception as e:
            show_warning(self, tr("common.error"), str(e))

    def _import_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("backup.import_btn"), "", tr("backup.file_filter")
        )
        if not path:
            return
        replace = confirm(self, tr("backup.import_title"), tr("backup.import_replace"))
        try:
            stats = import_backup(path, replace_existing=replace)
            show_info(
                self, tr("common.success"),
                tr("backup.imported", books=stats["books"], pdfs=stats["pdfs"]),
            )
        except Exception as e:
            show_warning(self, tr("common.error"), str(e))

    def _check_updates(self):
        info = check_for_updates()
        if info:
            show_info(
                self, tr("update.available_title"),
                tr("update.available_body", version=info["version"], notes=info.get("notes", "")),
            )
        else:
            show_info(self, tr("update.title"), tr("update.up_to_date"))

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("sync.choose_folder"))
        if folder:
            self._sync_folder.setText(folder)

    def _passphrase(self) -> str:
        return self._pass_input.text()

    def _configure_sync(self) -> bool:
        phrase = self._passphrase()
        folder = self._sync_folder.text().strip()
        if not phrase:
            show_warning(self, tr("settings.title"), tr("sync.passphrase_required"))
            return False
        if not folder:
            show_warning(self, tr("settings.title"), tr("sync.folder_required"))
            return False
        if is_sync_configured() and not check_passphrase(phrase):
            show_warning(self, tr("settings.title"), tr("sync.bad_passphrase"))
            return False
        if not is_sync_configured():
            setup_sync(phrase, folder)
        else:
            from app_settings import set_sync_folder, set_sync_enabled
            set_sync_folder(folder)
            set_sync_enabled(True)
        set_session_passphrase(phrase)
        return True

    def _do_sync(self):
        if not self._configure_sync():
            return
        try:
            stats, _ = sync_now()
            show_info(self, tr("sync.title"), tr("sync.done", **stats))
        except SyncError as e:
            key = f"sync.{e.args[0]}" if e.args else "sync.failed"
            show_warning(self, tr("sync.title"), tr(key))

    def _export_sync_backup(self):
        phrase = self._passphrase()
        if not phrase:
            show_warning(self, tr("settings.title"), tr("sync.passphrase_required"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("sync.export_btn"), "libooks-backup.enc", tr("sync.file_filter")
        )
        if not path:
            return
        try:
            export_to_file(path, phrase)
            show_info(self, tr("common.success"), tr("sync.exported", path=path))
        except Exception as e:
            show_warning(self, tr("common.error"), str(e))

    def _import_sync_backup(self):
        phrase = self._passphrase()
        if not phrase:
            show_warning(self, tr("settings.title"), tr("sync.passphrase_required"))
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("sync.import_btn"), "", tr("sync.file_filter")
        )
        if not path:
            return
        try:
            stats = import_from_file(path, phrase)
            show_info(self, tr("common.success"), tr("sync.done", **stats))
        except Exception as e:
            show_warning(self, tr("common.error"), str(e))

    def _save(self):
        lang = self._lang_combo.currentData()
        if lang != get_language():
            set_language(lang)

        if self._sync_enabled.isChecked():
            if not self._configure_sync():
                return
        else:
            clear_sync_secrets()
            set_session_passphrase(None)

        show_info(self, tr("settings.title"), tr("settings.saved"))
        self.accept()
