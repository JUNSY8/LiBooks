"""Metadatos y huella digital de archivos PDF."""

import hashlib
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_CHUNK = 1024 * 1024


def hash_archivo(ruta: str) -> Optional[str]:
    """SHA-256 del archivo; None si no se puede leer."""
    try:
        h = hashlib.sha256()
        with open(ruta, "rb") as f:
            while chunk := f.read(_CHUNK):
                h.update(chunk)
        return h.hexdigest()
    except OSError as e:
        logger.warning("No se pudo calcular hash de %s: %s", ruta, e)
        return None


def extraer_metadatos(ruta: str) -> Dict[str, str]:
    """Extrae título y autor del PDF si están disponibles."""
    titulo = ""
    autor = ""
    try:
        import fitz

        with fitz.open(ruta) as doc:
            meta = doc.metadata or {}
            titulo = (meta.get("title") or "").strip()
            autor = (meta.get("author") or "").strip()
    except Exception as e:
        logger.warning("No se pudieron leer metadatos de %s: %s", ruta, e)

    if not titulo:
        titulo = os.path.splitext(os.path.basename(ruta))[0]
    return {"titulo": titulo, "autor": autor}


def recoger_pdfs_en_carpeta(carpeta: str) -> list[str]:
    """Lista rutas PDF dentro de una carpeta (sin subcarpetas)."""
    if not os.path.isdir(carpeta):
        return []
    pdfs = []
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.lower().endswith(".pdf"):
            pdfs.append(os.path.join(carpeta, nombre))
    return pdfs
