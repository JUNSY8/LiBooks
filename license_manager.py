"""Gestión del ciclo de vida de la licencia en el equipo del usuario."""

import logging
import os
from typing import Optional

from paths import user_data_dir
from license_core import LicenseError, verify_license_key, format_license_info
from i18n import tr

logger = logging.getLogger(__name__)

LICENSE_FILE = os.path.join(user_data_dir(), "license.key")


def load_stored_license() -> Optional[str]:
    """Lee la licencia guardada localmente, si existe."""
    if not os.path.isfile(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError as e:
        logger.warning("No se pudo leer la licencia almacenada: %s", e)
        return None


def save_license(key: str) -> None:
    """Guarda una licencia válida en el directorio de datos del usuario."""
    os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        f.write(key.strip())


def clear_license() -> None:
    """Elimina la licencia almacenada."""
    if os.path.isfile(LICENSE_FILE):
        os.remove(LICENSE_FILE)


def get_active_license_info() -> Optional[dict]:
    """Devuelve el payload de la licencia activa o None."""
    key = load_stored_license()
    if not key:
        return None
    try:
        return verify_license_key(key)
    except LicenseError:
        return None


def activate_license(key: str) -> dict:
    """Valida y persiste una nueva clave de licencia."""
    payload = verify_license_key(key)
    save_license(key)
    logger.info("Licencia activada para: %s", payload.get("holder", "?"))
    return payload


def ensure_license_valid() -> dict:
    """Comprueba que exista una licencia válida almacenada.

    Raises:
        LicenseError: si no hay licencia o no es válida.
    """
    key = load_stored_license()
    if not key:
        raise LicenseError(tr("license.no_stored"))
    return verify_license_key(key)


def license_summary() -> str:
    """Resumen legible de la licencia activa."""
    payload = get_active_license_info()
    if not payload:
        return "Sin licencia activa"
    return format_license_info(payload)
