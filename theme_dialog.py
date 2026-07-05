"""Diálogo de personalización de colores y estilos guardados."""

from __future__ import annotations

from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
    QColorDialog,
)

from i18n import tr
from icons import set_button_icon
from styles import ACCENT_TEXT
from title_bar import FramelessDialog
from dialog_layout import DIALOG_PAGE_MARGINS, attach_footer_bar, compact_button_row
from message_boxes import wire_dialog_buttons, disable_button_default, show_warning, confirm
from color_theme import (
    BUILTIN_PRESETS,
    COLOR_GROUPS,
    activate_theme,
    default_palette,
    delete_custom_theme,
    get_active_theme_id,
    is_builtin_preset,
    list_available_themes,
    preset_palette,
    find_main_window,
    refresh_application_theme,
    resolve_palette,
    save_custom_theme,
    update_builtin_overrides,
)
from app_settings import get_active_theme_id as _get_active_theme_id


class _ColorSwatch(QPushButton):
    """Botón cuadrado que abre el selector de color."""

    def __init__(self, token: str, on_change=None, parent=None):
        super().__init__(parent)
        self.token = token
        self._on_change = on_change
        self._hex = "#000000"
        self.setObjectName("iconButton")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick_color)

    def set_hex(self, value: str) -> None:
        self._hex = value
        self.setToolTip(value)
        self.setStyleSheet(
            f"background-color: {value}; border: 1px solid rgba(255,255,255,0.25);"
            " border-radius: 8px;"
        )

    def hex(self) -> str:
        return self._hex

    def _pick_color(self) -> None:
        initial = QColor(self._hex)
        color = QColorDialog.getColor(initial, self, tr("theme.pick_color"))
        if color.isValid():
            self.set_hex(color.name())
            if self._on_change:
                self._on_change()


class ThemeDialog(FramelessDialog):
    """Editor de paleta con presets, colores por elemento y estilos guardados."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = find_main_window(parent)
        self.setMinimumSize(640, 520)
        self.setModal(True)
        self._init_frameless_dialog()
        self._swatches: Dict[str, _ColorSwatch] = {}
        self._group_labels: List[QLabel] = []
        self._token_labels: Dict[str, QLabel] = {}
        self._loading = False
        self._current_theme_id = _get_active_theme_id()
        self._snapshot_theme_id = self._current_theme_id
        self._build_ui()
        self.retranslate_ui()
        self._load_theme(self._current_theme_id)

    def _build_ui(self):
        outer = self.frameless_layout(margins=(0, 0, 0, 0), spacing=0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        form = QWidget()
        root = QVBoxLayout(form)
        root.setContentsMargins(*DIALOG_PAGE_MARGINS)
        root.setSpacing(14)

        self._hint = QLabel()
        self._hint.setObjectName("appSubtitle")
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)

        style_row = QHBoxLayout()
        style_row.setSpacing(10)
        self._style_label = QLabel()
        self._style_label.setObjectName("fieldLabel")
        self._style_combo = QComboBox()
        self._style_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._style_combo.currentIndexChanged.connect(self._on_style_changed)
        style_row.addWidget(self._style_label)
        style_row.addWidget(self._style_combo, 1)
        root.addLayout(style_row)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        self._preset_label = QLabel()
        self._preset_label.setObjectName("fieldLabel")
        self._preset_combo = QComboBox()
        self._preset_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self._preset_label)
        preset_row.addWidget(self._preset_combo, 1)
        root.addLayout(preset_row)

        self._colors_title = QLabel()
        self._colors_title.setObjectName("dialogTitle")
        root.addWidget(self._colors_title)

        colors_host = QWidget()
        self._colors_layout = QVBoxLayout(colors_host)
        self._colors_layout.setContentsMargins(0, 0, 0, 0)
        self._colors_layout.setSpacing(12)
        root.addWidget(colors_host)

        save_frame = QFrame()
        save_frame.setObjectName("dialogDivider")
        root.addWidget(save_frame)

        self._save_title = QLabel()
        self._save_title.setObjectName("dialogTitle")
        root.addWidget(self._save_title)

        name_row = QHBoxLayout()
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(tr("theme.name_placeholder"))
        self._btn_save_style = QPushButton()
        self._btn_save_style.setObjectName("secondaryButton")
        self._btn_save_style.clicked.connect(self._save_as_new)
        self._btn_save_style.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._btn_delete_style = QPushButton()
        self._btn_delete_style.setObjectName("dangerButton")
        self._btn_delete_style.clicked.connect(self._delete_current)
        self._btn_delete_style.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        name_row.addWidget(self._name_input, 1)
        root.addLayout(name_row)
        root.addLayout(compact_button_row(self._btn_save_style, self._btn_delete_style))

        actions = QHBoxLayout()
        self._btn_reset = QPushButton()
        self._btn_reset.setObjectName("ghostButton")
        self._btn_reset.clicked.connect(self._reset_preset)
        self._btn_reset.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        actions.addWidget(self._btn_reset)
        actions.addStretch()
        root.addLayout(actions)

        scroll.setWidget(form)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        self._btn_cancel = QPushButton()
        self._btn_cancel.setObjectName("secondaryButton")
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_apply = QPushButton()
        self._btn_apply.setObjectName("primaryButton")
        self._btn_apply.clicked.connect(self._apply_and_close)
        footer.addWidget(self._btn_cancel)
        footer.addWidget(self._btn_apply)
        attach_footer_bar(outer, footer)

        wire_dialog_buttons(self._btn_cancel, self._btn_apply)
        disable_button_default(self._btn_apply)

        self._build_color_rows()
        self._refresh_style_combo()

    def _build_color_rows(self):
        for group_key, tokens in COLOR_GROUPS:
            group_lbl = QLabel()
            group_lbl.setObjectName("fieldLabel")
            group_lbl.setProperty("group_key", group_key)
            self._group_labels.append(group_lbl)
            self._colors_layout.addWidget(group_lbl)

            grid_host = QWidget()
            grid = QGridLayout(grid_host)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)
            row_idx = 0
            for token in tokens:
                lbl = QLabel()
                lbl.setObjectName("appSubtitle")
                self._token_labels[token] = lbl
                swatch = _ColorSwatch(token, on_change=self._on_color_edited)
                self._swatches[token] = swatch
                grid.addWidget(lbl, row_idx, 0)
                grid.addWidget(swatch, row_idx, 1, Qt.AlignLeft)
                row_idx += 1
            self._colors_layout.addWidget(grid_host)

    def retranslate_ui(self):
        self.set_frameless_title(tr("theme.title"))
        self._hint.setText(tr("theme.hint"))
        self._style_label.setText(tr("theme.active_style"))
        self._preset_label.setText(tr("theme.base_preset"))
        self._colors_title.setText(tr("theme.colors_title"))
        self._save_title.setText(tr("theme.save_title"))
        self._btn_save_style.setText(tr("theme.save_as"))
        self._btn_delete_style.setText(tr("theme.delete_style"))
        self._btn_reset.setText(tr("theme.reset_preset"))
        self._btn_cancel.setText(tr("common.cancel"))
        set_button_icon(self._btn_apply, "check", 16, ACCENT_TEXT, tr("theme.apply"))

        for lbl in self._group_labels:
            group_key = lbl.property("group_key")
            if group_key:
                lbl.setText(tr(group_key))

        for token, lbl in self._token_labels.items():
            lbl.setText(tr(f"theme.color_{token}"))

        self._refresh_style_combo()
        self._refresh_preset_combo()

    def _refresh_style_combo(self):
        self._loading = True
        current = self._current_theme_id
        self._style_combo.blockSignals(True)
        self._style_combo.clear()
        for theme_id, name, _custom in list_available_themes():
            self._style_combo.addItem(name, theme_id)
        idx = self._style_combo.findData(current)
        if idx >= 0:
            self._style_combo.setCurrentIndex(idx)
        self._style_combo.blockSignals(False)
        self._loading = False
        self._update_delete_button()

    def _refresh_preset_combo(self):
        self._loading = True
        base = self._base_preset_for_current()
        self._preset_combo.blockSignals(True)
        self._preset_combo.clear()
        for preset_id, meta in BUILTIN_PRESETS.items():
            self._preset_combo.addItem(tr(meta["name_key"]), preset_id)
        idx = self._preset_combo.findData(base)
        if idx >= 0:
            self._preset_combo.setCurrentIndex(idx)
        self._preset_combo.blockSignals(False)
        self._loading = False

    def _base_preset_for_current(self) -> str:
        if self._current_theme_id.startswith("custom:"):
            from app_settings import get_custom_themes
            cid = self._current_theme_id[len("custom:"):]
            data = get_custom_themes().get(cid, {})
            base = data.get("base_preset", "libooks") if isinstance(data, dict) else "libooks"
            return base if base in BUILTIN_PRESETS else "libooks"
        return self._current_theme_id if is_builtin_preset(self._current_theme_id) else "libooks"

    def _update_delete_button(self):
        is_custom = self._current_theme_id.startswith("custom:")
        self._btn_delete_style.setEnabled(is_custom)
        self._preset_combo.setEnabled(not is_custom)

    def _load_theme(self, theme_id: str) -> None:
        self._loading = True
        self._current_theme_id = theme_id
        palette = resolve_palette(theme_id)
        for token, swatch in self._swatches.items():
            swatch.set_hex(palette.get(token, default_palette()[token]))
        if theme_id.startswith("custom:"):
            from app_settings import get_custom_themes
            cid = theme_id[len("custom:"):]
            data = get_custom_themes().get(cid, {})
            name = data.get("name", "") if isinstance(data, dict) else ""
            self._name_input.setText(name if isinstance(name, str) else "")
        else:
            preset = BUILTIN_PRESETS.get(theme_id, {})
            self._name_input.setText(tr(preset.get("name_key", "theme.preset_libooks")))
        self._refresh_preset_combo()
        self._update_delete_button()
        self._loading = False

    def _collect_colors(self) -> Dict[str, str]:
        return {token: swatch.hex() for token, swatch in self._swatches.items()}

    def _on_style_changed(self, _index: int) -> None:
        if self._loading:
            return
        theme_id = self._style_combo.currentData()
        if theme_id:
            self._load_theme(theme_id)

    def _on_preset_changed(self, _index: int) -> None:
        if self._loading or self._current_theme_id.startswith("custom:"):
            return
        preset_id = self._preset_combo.currentData()
        if not preset_id:
            return
        palette = preset_palette(preset_id)
        for token, swatch in self._swatches.items():
            swatch.set_hex(palette[token])

    def _on_color_edited(self) -> None:
        if self._loading:
            return
        self._apply_live()

    def _apply_live(self) -> None:
        from color_theme import apply_palette
        apply_palette(self._collect_colors())
        refresh_application_theme(self._main_window)

    def _reset_preset(self) -> None:
        base = self._preset_combo.currentData() or "libooks"
        palette = preset_palette(base)
        for token, swatch in self._swatches.items():
            swatch.set_hex(palette[token])
        self._apply_live()

    def _save_as_new(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            show_warning(self, tr("theme.title"), tr("theme.name_required"))
            return
        base = self._preset_combo.currentData() or "libooks"
        colors = self._collect_colors()
        cid = save_custom_theme(name, colors, base)
        self._current_theme_id = f"custom:{cid}"
        self._refresh_style_combo()
        idx = self._style_combo.findData(self._current_theme_id)
        if idx >= 0:
            self._style_combo.setCurrentIndex(idx)
        self._update_delete_button()

    def _delete_current(self) -> None:
        if not self._current_theme_id.startswith("custom:"):
            return
        if not confirm(self, tr("theme.title"), tr("theme.delete_confirm")):
            return
        delete_custom_theme(self._current_theme_id)
        self._current_theme_id = get_active_theme_id()
        self._refresh_style_combo()
        self._load_theme(self._current_theme_id)

    def _apply_and_close(self) -> None:
        theme_id = self._style_combo.currentData() or self._current_theme_id
        colors = self._collect_colors()
        if isinstance(theme_id, str) and theme_id.startswith("custom:"):
            from app_settings import get_custom_themes
            cid = theme_id[len("custom:"):]
            data = get_custom_themes().get(cid, {})
            base = data.get("base_preset", "libooks") if isinstance(data, dict) else "libooks"
            name = self._name_input.text().strip() or (
                data.get("name", tr("theme.unnamed")) if isinstance(data, dict) else tr("theme.unnamed")
            )
            save_custom_theme(name, colors, base, theme_id=cid)
        elif isinstance(theme_id, str) and is_builtin_preset(theme_id):
            update_builtin_overrides(theme_id, colors)
        activate_theme(theme_id, self.parent())
        self.accept()

    def reject(self):
        activate_theme(self._snapshot_theme_id, self.parent())
        super().reject()


def open_theme_dialog(parent=None) -> bool:
    dlg = ThemeDialog(parent)
    return dlg.exec_() == QDialog.Accepted
