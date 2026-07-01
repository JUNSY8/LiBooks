"""Comprobación de actualizaciones (manifest JSON remoto)."""

import json
import logging
import urllib.request
from typing import Optional, Dict

from version import APP_VERSION

logger = logging.getLogger(__name__)

# Sustituir por la URL real del manifest al publicar releases.
DEFAULT_UPDATE_MANIFEST_URL = (
    "https://raw.githubusercontent.com/JUNSY/LiBooks/main/release/version.json"
)


def _parse_version(version: str) -> tuple:
    parts = []
    for p in version.strip().lstrip("v").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote: str, current: str = APP_VERSION) -> bool:
    return _parse_version(remote) > _parse_version(current)


def check_for_updates(url: str = DEFAULT_UPDATE_MANIFEST_URL,
                      timeout: float = 8.0) -> Optional[Dict[str, str]]:
    """Devuelve info de actualización si hay versión más nueva."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"LiBooks/{APP_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        remote_ver = data.get("version", "")
        if remote_ver and is_newer(remote_ver):
            return {
                "version": remote_ver,
                "url": data.get("download_url", ""),
                "notes": data.get("notes", ""),
            }
    except Exception as e:
        logger.info("No se pudo comprobar actualizaciones: %s", e)
    return None
