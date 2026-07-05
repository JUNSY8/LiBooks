"""Temas de color: paletas predefinidas, estilos personalizados y aplicación dinámica."""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app_settings import (
    delete_custom_theme as _delete_custom_theme,
    get_active_theme_id,
    get_custom_themes,
    get_theme_overrides,
    save_custom_theme as _save_custom_theme,
    set_active_theme_id,
    set_theme_overrides,
)

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")

# ── Tokens de color (clave interna → constante en styles.py) ───────────────

COLOR_TOKEN_ATTRS: Dict[str, str] = {
    "bg_main": "BG_MAIN",
    "bg_secondary": "BG_SECONDARY",
    "bg_input": "BG_INPUT",
    "bg_input_alt": "BG_INPUT_ALT",
    "bg_sidebar": "BG_SIDEBAR",
    "bg_tag": "BG_TAG",
    "bg_tag_hover": "BG_TAG_HOVER",
    "accent": "ACCENT",
    "accent_hover": "ACCENT_HOVER",
    "accent_text": "ACCENT_TEXT",
    "text_primary": "TEXT_PRIMARY",
    "text_secondary": "TEXT_SECONDARY",
    "text_label": "TEXT_LABEL",
    "danger": "DANGER",
    "danger_border": "DANGER_BORDER",
    "danger_hover": "DANGER_HOVER",
    "border_subtle": "BORDER_SUBTLE",
    "title_bar_icon": "TITLE_BAR_ICON",
    "title_bar_icon_hover": "TITLE_BAR_ICON_HOVER",
    "title_bar_close": "TITLE_BAR_CLOSE",
    "title_bar_close_pressed": "TITLE_BAR_CLOSE_PRESSED",
    "status_unread_bg": "STATUS_UNREAD_BG",
    "status_unread_text": "STATUS_UNREAD_TEXT",
    "status_unread_hover": "STATUS_UNREAD_HOVER",
    "status_reading_bg": "STATUS_READING_BG",
    "status_reading_text": "STATUS_READING_TEXT",
    "status_reading_hover": "STATUS_READING_HOVER",
    "status_completed_bg": "STATUS_COMPLETED_BG",
    "status_completed_text": "STATUS_COMPLETED_TEXT",
    "status_completed_hover": "STATUS_COMPLETED_HOVER",
    "status_paused_bg": "STATUS_PAUSED_BG",
    "status_paused_text": "STATUS_PAUSED_TEXT",
    "status_paused_hover": "STATUS_PAUSED_HOVER",
    "status_abandoned_bg": "STATUS_ABANDONED_BG",
    "status_abandoned_text": "STATUS_ABANDONED_TEXT",
    "status_abandoned_hover": "STATUS_ABANDONED_HOVER",
}

COLOR_GROUPS: List[Tuple[str, List[str]]] = [
    ("theme.group_surfaces", [
        "bg_main", "bg_secondary", "bg_input", "bg_input_alt", "bg_sidebar",
        "bg_tag", "bg_tag_hover",
    ]),
    ("theme.group_accent", [
        "accent", "accent_hover", "accent_text",
    ]),
    ("theme.group_text", [
        "text_primary", "text_secondary", "text_label",
    ]),
    ("theme.group_danger", [
        "danger", "danger_border", "danger_hover",
    ]),
    ("theme.group_chrome", [
        "border_subtle", "title_bar_icon", "title_bar_icon_hover",
        "title_bar_close", "title_bar_close_pressed",
    ]),
    ("theme.group_status_unread", [
        "status_unread_bg", "status_unread_text", "status_unread_hover",
    ]),
    ("theme.group_status_reading", [
        "status_reading_bg", "status_reading_text", "status_reading_hover",
    ]),
    ("theme.group_status_completed", [
        "status_completed_bg", "status_completed_text", "status_completed_hover",
    ]),
    ("theme.group_status_paused", [
        "status_paused_bg", "status_paused_text", "status_paused_hover",
    ]),
    ("theme.group_status_abandoned", [
        "status_abandoned_bg", "status_abandoned_text", "status_abandoned_hover",
    ]),
]

DEFAULT_PALETTE: Dict[str, str] = {
    "bg_main": "#121e24",
    "bg_secondary": "#1e2d36",
    "bg_input": "#1a2a33",
    "bg_input_alt": "#243436",
    "bg_sidebar": "#0f1a20",
    "bg_tag": "#065f46",
    "bg_tag_hover": "#087a5a",
    "accent": "#4adea9",
    "accent_hover": "#34d399",
    "accent_text": "#0f172a",
    "text_primary": "#ffffff",
    "text_secondary": "#9ca3af",
    "text_label": "#94a3b8",
    "danger": "#f87171",
    "danger_border": "#ef4444",
    "danger_hover": "#fca5a5",
    "border_subtle": "#2a3f4a",
    "title_bar_icon": "#a8b4be",
    "title_bar_icon_hover": "#e8eef2",
    "title_bar_close": "#e81123",
    "title_bar_close_pressed": "#bf0f1d",
    "status_unread_bg": "#374151",
    "status_unread_text": "#d1d5db",
    "status_unread_hover": "#3f4b5e",
    "status_reading_bg": "#1e3a5f",
    "status_reading_text": "#93c5fd",
    "status_reading_hover": "#214068",
    "status_completed_bg": "#064e3b",
    "status_completed_text": "#6ee7b7",
    "status_completed_hover": "#075641",
    "status_paused_bg": "#78350f",
    "status_paused_text": "#fcd34d",
    "status_paused_hover": "#843a10",
    "status_abandoned_bg": "#4c1d24",
    "status_abandoned_text": "#fca5a5",
    "status_abandoned_hover": "#542028",
}

BUILTIN_PRESETS: Dict[str, Dict[str, Any]] = {
    "libooks": {
        "name_key": "theme.preset_libooks",
        "colors": DEFAULT_PALETTE,
    },
    "ocean": {
        "name_key": "theme.preset_ocean",
        "colors": {
            **DEFAULT_PALETTE,
            "bg_main": "#0f172a",
            "bg_secondary": "#1e293b",
            "bg_input": "#172033",
            "bg_input_alt": "#243044",
            "bg_sidebar": "#0b1220",
            "bg_tag": "#1e3a5f",
            "accent": "#38bdf8",
            "accent_hover": "#0ea5e9",
            "accent_text": "#082f49",
            "border_subtle": "#334155",
        },
    },
    "violet": {
        "name_key": "theme.preset_violet",
        "colors": {
            **DEFAULT_PALETTE,
            "bg_main": "#15121f",
            "bg_secondary": "#221c33",
            "bg_input": "#1c1729",
            "bg_input_alt": "#2a223d",
            "bg_sidebar": "#100d18",
            "bg_tag": "#4c1d95",
            "accent": "#c084fc",
            "accent_hover": "#a855f7",
            "accent_text": "#1e1033",
            "border_subtle": "#3b3254",
        },
    },
    "amber": {
        "name_key": "theme.preset_amber",
        "colors": {
            **DEFAULT_PALETTE,
            "bg_main": "#1a1510",
            "bg_secondary": "#2a2218",
            "bg_input": "#231c14",
            "bg_input_alt": "#332818",
            "bg_sidebar": "#14100c",
            "bg_tag": "#78350f",
            "accent": "#fbbf24",
            "accent_hover": "#f59e0b",
            "accent_text": "#422006",
            "border_subtle": "#443728",
        },
    },
    "rose": {
        "name_key": "theme.preset_rose",
        "colors": {
            **DEFAULT_PALETTE,
            "bg_main": "#1a1216",
            "bg_secondary": "#2a1c22",
            "bg_input": "#23181c",
            "bg_input_alt": "#35242c",
            "bg_sidebar": "#140e11",
            "bg_tag": "#881337",
            "accent": "#fb7185",
            "accent_hover": "#f43f5e",
            "accent_text": "#4c0519",
            "border_subtle": "#443038",
        },
    },
    "forest": {
        "name_key": "theme.preset_forest",
        "colors": {
            **DEFAULT_PALETTE,
            "bg_main": "#101814",
            "bg_secondary": "#1a2620",
            "bg_input": "#152019",
            "bg_input_alt": "#1f2e28",
            "bg_sidebar": "#0c1210",
            "bg_tag": "#14532d",
            "accent": "#86efac",
            "accent_hover": "#4ade80",
            "accent_text": "#052e16",
            "border_subtle": "#2a3f36",
        },
    },
}


def normalize_hex(value: str) -> str:
    """Normaliza un color hex (#RRGGBB)."""
    if not value:
        raise ValueError("empty color")
    raw = value.strip()
    if not _HEX_RE.match(raw):
        raise ValueError(f"invalid hex color: {value}")
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if len(raw) == 4:
        raw = "#" + "".join(ch * 2 for ch in raw[1:])
    return raw.lower()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = normalize_hex(hex_color)[1:]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba_from_hex(hex_color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def default_palette() -> Dict[str, str]:
    return copy.deepcopy(DEFAULT_PALETTE)


def is_builtin_preset(theme_id: str) -> bool:
    return theme_id in BUILTIN_PRESETS


def preset_palette(preset_id: str) -> Dict[str, str]:
    preset = BUILTIN_PRESETS.get(preset_id)
    if not preset:
        return default_palette()
    return copy.deepcopy(preset["colors"])


def resolve_palette(theme_id: Optional[str] = None) -> Dict[str, str]:
    """Combina preset base + overrides del estilo activo."""
    tid = theme_id or get_active_theme_id()
    if tid.startswith("custom:"):
        custom_id = tid[len("custom:"):]
        custom = get_custom_themes().get(custom_id, {})
        base_id = custom.get("base_preset", "libooks")
        palette = preset_palette(base_id)
        colors = custom.get("colors", {})
        if isinstance(colors, dict):
            for key, val in colors.items():
                if key in COLOR_TOKEN_ATTRS and isinstance(val, str):
                    try:
                        palette[key] = normalize_hex(val)
                    except ValueError:
                        pass
        return palette

    palette = preset_palette(tid if is_builtin_preset(tid) else "libooks")
    overrides = get_theme_overrides(tid)
    if isinstance(overrides, dict):
        for key, val in overrides.items():
            if key in COLOR_TOKEN_ATTRS and isinstance(val, str):
                try:
                    palette[key] = normalize_hex(val)
                except ValueError:
                    pass
    return palette


def apply_palette(palette: Dict[str, str]) -> None:
    """Actualiza las constantes del módulo styles."""
    from styles import apply_color_palette

    cleaned: Dict[str, str] = {}
    for key in COLOR_TOKEN_ATTRS:
        if key in palette:
            cleaned[key] = normalize_hex(palette[key])
    apply_color_palette(cleaned)


def find_main_window(widget=None):
    """Busca la ventana principal subiendo la jerarquia de widgets."""
    from PyQt5.QtWidgets import QWidget

    current = widget
    while isinstance(current, QWidget):
        if hasattr(current, "refresh_theme"):
            return current
        current = current.parent()
    return None


def refresh_application_theme(main_window=None) -> None:
    """Reaplica la hoja de estilos y actualiza iconos de la ventana principal."""
    from PyQt5.QtWidgets import QApplication

    from styles import app_stylesheet

    resolved = main_window
    if resolved is not None and not hasattr(resolved, "refresh_theme"):
        resolved = find_main_window(resolved)

    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(app_stylesheet())

    if resolved is not None and hasattr(resolved, "refresh_theme"):
        resolved.refresh_theme()


def load_active_theme() -> Dict[str, str]:
    palette = resolve_palette()
    apply_palette(palette)
    return palette


def list_available_themes() -> List[Tuple[str, str, bool]]:
    """Devuelve (id, nombre traducido, es_personalizado)."""
    from i18n import tr

    items: List[Tuple[str, str, bool]] = []
    for preset_id, meta in BUILTIN_PRESETS.items():
        items.append((preset_id, tr(meta["name_key"]), False))
    for custom_id, data in get_custom_themes().items():
        name = data.get("name") if isinstance(data, dict) else None
        if not isinstance(name, str) or not name.strip():
            name = tr("theme.unnamed")
        items.append((f"custom:{custom_id}", name.strip(), True))
    return items


def activate_theme(theme_id: str, main_window=None) -> None:
    set_active_theme_id(theme_id)
    apply_palette(resolve_palette(theme_id))
    refresh_application_theme(main_window)


def save_custom_theme(name: str, colors: Dict[str, str], base_preset: str = "libooks",
                      theme_id: Optional[str] = None) -> str:
    cid = theme_id or str(uuid.uuid4())[:8]
    cleaned: Dict[str, str] = {}
    base = preset_palette(base_preset)
    for key in COLOR_TOKEN_ATTRS:
        raw = colors.get(key, base.get(key))
        if isinstance(raw, str):
            cleaned[key] = normalize_hex(raw)
    _save_custom_theme(cid, name.strip(), cleaned, base_preset)
    return cid


def delete_custom_theme(theme_id: str) -> None:
    if not theme_id.startswith("custom:"):
        return
    cid = theme_id[len("custom:"):]
    _delete_custom_theme(cid)
    if get_active_theme_id() == theme_id:
        activate_theme("libooks")


def update_builtin_overrides(theme_id: str, colors: Dict[str, str]) -> None:
    """Guarda personalizaciones sobre un preset integrado."""
    if not is_builtin_preset(theme_id):
        return
    cleaned: Dict[str, str] = {}
    base = preset_palette(theme_id)
    for key, val in colors.items():
        if key not in COLOR_TOKEN_ATTRS or not isinstance(val, str):
            continue
        try:
            normalized = normalize_hex(val)
        except ValueError:
            continue
        if normalized != base.get(key):
            cleaned[key] = normalized
    set_theme_overrides(theme_id, cleaned)
