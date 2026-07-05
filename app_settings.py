"""Preferencias de usuario persistidas en settings.json."""

import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from paths import user_data_dir

logger = logging.getLogger(__name__)

_SETTINGS_PATH = os.path.join(user_data_dir(), "settings.json")
DEFAULT_LIBRARY_VIEW = "grid"
DEFAULT_LIBRARY_SORT = "title_asc"
DEFAULT_LIBRARY_FILTER = "all"


def _read() -> Dict[str, Any]:
    if not os.path.isfile(_SETTINGS_PATH):
        return {}
    try:
        with open(_SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("No se pudo leer settings.json: %s", e)
        return {}


def _write(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_setting(key: str, default: Any = None) -> Any:
    return _read().get(key, default)


def set_setting(key: str, value: Any) -> None:
    data = _read()
    data[key] = value
    _write(data)


def get_library_view() -> str:
    mode = get_setting("library_view", DEFAULT_LIBRARY_VIEW)
    return mode if mode in ("grid", "list") else DEFAULT_LIBRARY_VIEW


def set_library_view(mode: str) -> None:
    if mode in ("grid", "list"):
        set_setting("library_view", mode)


def get_library_sort() -> str:
    allowed = (
        "title_asc", "title_desc", "author_asc", "date_added_desc",
        "date_added_asc", "last_read_desc", "progress_desc", "progress_asc",
    )
    val = get_setting("library_sort", DEFAULT_LIBRARY_SORT)
    return val if val in allowed else DEFAULT_LIBRARY_SORT


def set_library_sort(sort_key: str) -> None:
    if sort_key in (
        "title_asc", "title_desc", "author_asc", "date_added_desc",
        "date_added_asc", "last_read_desc", "progress_desc", "progress_asc",
    ):
        set_setting("library_sort", sort_key)


def get_library_filter() -> str:
    val = get_setting("library_filter", DEFAULT_LIBRARY_FILTER)
    return val if val in ("all", "reading", "completed", "unread") else DEFAULT_LIBRARY_FILTER


def set_library_filter(filter_key: str) -> None:
    if filter_key in ("all", "reading", "completed", "unread"):
        set_setting("library_filter", filter_key)


def get_library_tag_filter() -> Optional[int]:
    val = get_setting("library_tag_filter")
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def set_library_tag_filter(tag_id: Optional[int]) -> None:
    if tag_id is None:
        data = _read()
        data.pop("library_tag_filter", None)
        _write(data)
    else:
        set_setting("library_tag_filter", tag_id)


def get_library_rating_filter() -> Optional[int]:
    val = get_setting("library_rating_filter")
    if val is None:
        val = get_setting("library_brillo_filter")
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def set_library_rating_filter(rating: Optional[int]) -> None:
    data = _read()
    data.pop("library_brillo_filter", None)
    if rating is None:
        data.pop("library_rating_filter", None)
    else:
        data["library_rating_filter"] = rating
    _write(data)


# ── Sincronización cifrada ─────────────────────────────────────────────────

def get_sync_enabled() -> bool:
    return bool(get_setting("sync_enabled", False))


def set_sync_enabled(enabled: bool) -> None:
    set_setting("sync_enabled", bool(enabled))


def get_sync_folder() -> Optional[str]:
    folder = get_setting("sync_folder")
    return folder if folder and os.path.isdir(folder) else folder


def set_sync_folder(folder: Optional[str]) -> None:
    if folder:
        set_setting("sync_folder", folder)
    else:
        data = _read()
        data.pop("sync_folder", None)
        _write(data)


def get_sync_salt() -> Optional[str]:
    return get_setting("sync_salt")


def set_sync_salt(salt_b64: str) -> None:
    set_setting("sync_salt", salt_b64)


def get_sync_verifier() -> Optional[str]:
    return get_setting("sync_verifier")


def set_sync_verifier(verifier: str) -> None:
    set_setting("sync_verifier", verifier)


def get_sync_device_id() -> Optional[str]:
    return get_setting("sync_device_id")


def ensure_sync_device_id() -> str:
    device_id = get_sync_device_id()
    if not device_id:
        device_id = str(uuid.uuid4())
        set_setting("sync_device_id", device_id)
    return device_id


def clear_sync_secrets() -> None:
    data = _read()
    for key in ("sync_enabled", "sync_folder", "sync_salt", "sync_verifier"):
        data.pop(key, None)
    _write(data)


# ── OCR (Tesseract) ────────────────────────────────────────────────────────

def get_tesseract_tessdata_path() -> Optional[str]:
    """Ruta personalizada a tessdata; None = detección automática."""
    folder = get_setting("tesseract_tessdata_path")
    if folder and os.path.isdir(folder):
        return folder
    return None


def set_tesseract_tessdata_path(folder: Optional[str]) -> None:
    if folder:
        set_setting("tesseract_tessdata_path", folder)
    else:
        data = _read()
        data.pop("tesseract_tessdata_path", None)
        _write(data)


# ── Tour guiado y ayudas visuales ──────────────────────────────────────────

_TOUR_SECTIONS = (
    "navigation", "library", "stats", "collections", "pdf",
    "book_add", "book_edit", "collection_create", "collection_edit",
    "settings",
)


def get_help_tips_enabled() -> bool:
    return not bool(get_setting("help_tips_disabled", False))


def set_help_tips_enabled(enabled: bool) -> None:
    set_setting("help_tips_disabled", not enabled)
    if not enabled:
        mark_all_tour_sections_seen()


def _tour_sections_seen() -> Dict[str, bool]:
    seen = get_setting("tour_sections_seen", {})
    return seen if isinstance(seen, dict) else {}


def is_tour_section_seen(section: str) -> bool:
    return bool(_tour_sections_seen().get(section, False))


def mark_tour_section_seen(section: str) -> None:
    data = _read()
    seen = data.get("tour_sections_seen", {})
    if not isinstance(seen, dict):
        seen = {}
    if seen.get(section):
        return
    seen[section] = True
    data["tour_sections_seen"] = seen
    _write(data)


def mark_all_tour_sections_seen() -> None:
    set_setting("tour_sections_seen", {s: True for s in _TOUR_SECTIONS})


def reset_tour_sections() -> None:
    data = _read()
    data.pop("tour_sections_seen", None)
    _write(data)


# ── Filtros oculares (visor PDF) ───────────────────────────────────────────

def get_pdf_eye_comfort_mode() -> str:
    from eye_comfort import DEFAULT_MODE, normalize_mode
    return normalize_mode(get_setting("pdf_eye_comfort_mode", DEFAULT_MODE))


def set_pdf_eye_comfort_mode(mode: str) -> None:
    from eye_comfort import normalize_mode
    set_setting("pdf_eye_comfort_mode", normalize_mode(mode))


def get_pdf_eye_comfort_intensity() -> int:
    from eye_comfort import DEFAULT_INTENSITY, normalize_intensity
    return normalize_intensity(get_setting("pdf_eye_comfort_intensity", DEFAULT_INTENSITY))


def set_pdf_eye_comfort_intensity(value: int) -> None:
    from eye_comfort import normalize_intensity
    set_setting("pdf_eye_comfort_intensity", normalize_intensity(value))


# ── Temas de color ─────────────────────────────────────────────────────────

DEFAULT_THEME_ID = "libooks"


def get_active_theme_id() -> str:
    val = get_setting("active_theme_id", DEFAULT_THEME_ID)
    return val if isinstance(val, str) and val else DEFAULT_THEME_ID


def set_active_theme_id(theme_id: str) -> None:
    set_setting("active_theme_id", theme_id)


def get_custom_themes() -> Dict[str, Any]:
    raw = get_setting("custom_themes", {})
    return raw if isinstance(raw, dict) else {}


def save_custom_theme(theme_id: str, name: str, colors: Dict[str, str],
                      base_preset: str = DEFAULT_THEME_ID) -> None:
    data = _read()
    themes = data.get("custom_themes", {})
    if not isinstance(themes, dict):
        themes = {}
    themes[theme_id] = {
        "name": name,
        "base_preset": base_preset,
        "colors": colors,
    }
    data["custom_themes"] = themes
    _write(data)


def delete_custom_theme(theme_id: str) -> None:
    data = _read()
    themes = data.get("custom_themes", {})
    if isinstance(themes, dict):
        themes.pop(theme_id, None)
        data["custom_themes"] = themes
    _write(data)


def get_theme_overrides(theme_id: str) -> Dict[str, str]:
    raw = get_setting("theme_overrides", {})
    if not isinstance(raw, dict):
        return {}
    overrides = raw.get(theme_id, {})
    return overrides if isinstance(overrides, dict) else {}


def set_theme_overrides(theme_id: str, overrides: Dict[str, str]) -> None:
    data = _read()
    all_overrides = data.get("theme_overrides", {})
    if not isinstance(all_overrides, dict):
        all_overrides = {}
    if overrides:
        all_overrides[theme_id] = overrides
    else:
        all_overrides.pop(theme_id, None)
    data["theme_overrides"] = all_overrides
    _write(data)

