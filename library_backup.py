"""Exportación e importación de copias de seguridad de la biblioteca."""

import json
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, Optional

from paths import user_data_dir, PDF_FOLDER, DB_PATH
from version import APP_VERSION

logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.json"
DB_NAME = "libooks.db"


def _manifest() -> dict:
    from crud import obtener_libros, ruta_absoluta_libro
    books = []
    for libro in obtener_libros():
        ruta = ruta_absoluta_libro(libro)
        books.append({
            "titulo": libro.titulo,
            "archivo_pdf": libro.archivo_pdf,
            "file_hash": libro.file_hash,
            "has_file": bool(ruta and os.path.isfile(ruta)),
        })
    return {
        "version": 1,
        "app_version": APP_VERSION,
        "exported_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "books": books,
    }


def export_backup(dest_zip: str, include_pdfs: bool = True) -> Dict[str, int]:
    """Crea un .zip con la base de datos y opcionalmente los PDFs."""
    stats = {"books": 0, "pdfs": 0}
    os.makedirs(os.path.dirname(os.path.abspath(dest_zip)) or ".", exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = _manifest()
        stats["books"] = len(manifest["books"])
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))
        if os.path.isfile(DB_PATH):
            zf.write(DB_PATH, DB_NAME)
        if include_pdfs:
            for libro in manifest["books"]:
                nombre = libro.get("archivo_pdf")
                if not nombre:
                    continue
                ruta = os.path.join(PDF_FOLDER, nombre)
                if os.path.isfile(ruta):
                    zf.write(ruta, f"libros/{nombre}")
                    stats["pdfs"] += 1
    return stats


def _validate_zip(zf: zipfile.ZipFile) -> dict:
    if MANIFEST_NAME not in zf.namelist():
        raise ValueError("manifest_missing")
    manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
    if DB_NAME not in zf.namelist():
        raise ValueError("database_missing")
    return manifest


def import_backup(src_zip: str, replace_existing: bool = False) -> Dict[str, int]:
    """Restaura una copia de seguridad. Requiere reiniciar la app para aplicar BD."""
    stats = {"books": 0, "pdfs": 0}
    with zipfile.ZipFile(src_zip, "r") as zf:
        manifest = _validate_zip(zf)
        stats["books"] = len(manifest.get("books", []))

        with tempfile.TemporaryDirectory() as tmp:
            db_tmp = os.path.join(tmp, DB_NAME)
            zf.extract(DB_NAME, tmp)
            if replace_existing:
                shutil.copy2(db_tmp, DB_PATH)
            else:
                _merge_database(db_tmp)

            for name in zf.namelist():
                if not name.startswith("libros/") or name.endswith("/"):
                    continue
                nombre = os.path.basename(name)
                dest = os.path.join(PDF_FOLDER, nombre)
                if replace_existing or not os.path.isfile(dest):
                    os.makedirs(PDF_FOLDER, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    stats["pdfs"] += 1
    return stats


def _merge_database(backup_db: str) -> None:
    """Fusiona libros del backup que no existan localmente (por file_hash o nombre)."""
    src = sqlite3.connect(backup_db)
    dst = sqlite3.connect(DB_PATH)
    try:
        src.row_factory = sqlite3.Row
        rows = src.execute(
            "SELECT titulo, archivo_pdf, file_hash, paginas_leidas, total_paginas "
            "FROM libro"
        ).fetchall()
        for row in rows:
            exists = None
            if row["file_hash"]:
                exists = dst.execute(
                    "SELECT id_libro FROM libro WHERE file_hash = ?",
                    (row["file_hash"],),
                ).fetchone()
            if not exists:
                exists = dst.execute(
                    "SELECT id_libro FROM libro WHERE archivo_pdf = ?",
                    (row["archivo_pdf"],),
                ).fetchone()
            if exists:
                continue
            dst.execute(
                "INSERT INTO libro (titulo, archivo_pdf, file_hash, paginas_leidas, "
                "total_paginas) VALUES (?, ?, ?, ?, ?)",
                (
                    row["titulo"], row["archivo_pdf"], row["file_hash"],
                    row["paginas_leidas"] or 0, row["total_paginas"],
                ),
            )
        dst.commit()
    finally:
        src.close()
        dst.close()
