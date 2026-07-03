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


def get_library_brillo_filter() -> Optional[int]:
    val = get_setting("library_brillo_filter")
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def set_library_brillo_filter(brillo: Optional[int]) -> None:
    if brillo is None:
        data = _read()
        data.pop("library_brillo_filter", None)
        _write(data)
    else:
        set_setting("library_brillo_filter", brillo)


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
