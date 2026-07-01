"""Internacionalización LiBooks — traducciones JSON, inglés por defecto."""

import json
import logging
import os
from typing import Callable, Dict, List, Optional

from paths import resource_path, user_data_dir

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Español",
}

_settings_path = os.path.join(user_data_dir(), "settings.json")
_current_lang = DEFAULT_LANGUAGE
_strings: Dict[str, str] = {}
_callbacks: List[Callable[[], None]] = []


def _load_json(lang: str) -> Dict[str, str]:
    path = resource_path(os.path.join("locales", f"{lang}.json"))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def init_i18n() -> str:
    """Carga idioma guardado (o inglés) y las traducciones."""
    global _current_lang
    saved = DEFAULT_LANGUAGE
    if os.path.isfile(_settings_path):
        try:
            with open(_settings_path, encoding="utf-8") as f:
                data = json.load(f)
            lang = data.get("language", DEFAULT_LANGUAGE)
            if lang in SUPPORTED_LANGUAGES:
                saved = lang
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("No se pudo leer settings.json: %s", e)
    set_language(saved, persist=False)
    return _current_lang


def get_language() -> str:
    return _current_lang


def available_languages() -> Dict[str, str]:
    return dict(SUPPORTED_LANGUAGES)


def register_language_callback(callback: Callable[[], None]) -> None:
    if callback not in _callbacks:
        _callbacks.append(callback)


def set_language(lang: str, persist: bool = True) -> None:
    global _current_lang, _strings
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    _current_lang = lang
    try:
        _strings = _load_json(lang)
    except OSError as e:
        logger.error("No se pudo cargar locale %s: %s", lang, e)
        if lang != DEFAULT_LANGUAGE:
            _strings = _load_json(DEFAULT_LANGUAGE)
            _current_lang = DEFAULT_LANGUAGE
        else:
            _strings = {}

    if persist:
        os.makedirs(os.path.dirname(_settings_path), exist_ok=True)
        with open(_settings_path, "w", encoding="utf-8") as f:
            json.dump({"language": _current_lang}, f, indent=2)

    for cb in _callbacks:
        try:
            cb()
        except Exception as e:
            logger.exception("Error en callback de idioma: %s", e)


def tr(key: str, **kwargs) -> str:
    """Traduce una clave. Devuelve la clave si no existe."""
    text = _strings.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text
