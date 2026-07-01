"""Importación de PDFs: archivo único, carpeta y arrastrar/soltar."""

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

from crud import crear_libro_pdf, es_duplicado
from pdf_meta import extraer_metadatos, recoger_pdfs_en_carpeta

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    added: int = 0
    duplicates: int = 0
    failed: int = 0
    duplicate_titles: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def importar_pdf_directo(ruta: str) -> str:
    """Importa un PDF con metadatos automáticos. Devuelve estado: added|duplicate|failed."""
    if not os.path.isfile(ruta) or not ruta.lower().endswith(".pdf"):
        return "failed"
    existente = es_duplicado(ruta)
    if existente:
        return "duplicate"
    libro = crear_libro_pdf(ruta)
    return "added" if libro else "failed"


def importar_pdf_con_dialogo(ruta: str, titulo: str, autor: str, genero: str):
    """Importa con datos del formulario. Devuelve added|duplicate|failed."""
    existente = es_duplicado(ruta)
    if existente:
        return "duplicate", existente
    libro = crear_libro_pdf(
        ruta,
        titulo=titulo or None,
        nombre_autor=autor or None,
        nombre_genero=genero or None,
    )
    if libro:
        return "added", libro
    return "failed", None


def metadatos_para_formulario(ruta: str) -> tuple[str, str]:
    """Título y autor sugeridos para el diálogo de añadir libro."""
    meta = extraer_metadatos(ruta)
    return meta.get("titulo", ""), meta.get("autor", "")


def importar_varios(rutas: List[str]) -> ImportResult:
    """Importa varios PDFs sin diálogo (carpeta, drag & drop)."""
    result = ImportResult()
    for ruta in rutas:
        if not ruta.lower().endswith(".pdf"):
            continue
        existente = es_duplicado(ruta)
        if existente:
            result.duplicates += 1
            result.duplicate_titles.append(existente.titulo)
            continue
        try:
            libro = crear_libro_pdf(ruta)
            if libro:
                result.added += 1
            else:
                result.failed += 1
                result.errors.append(os.path.basename(ruta))
        except Exception as e:
            logger.exception("Error al importar %s: %s", ruta, e)
            result.failed += 1
            result.errors.append(os.path.basename(ruta))
    return result


def importar_carpeta(carpeta: str) -> ImportResult:
    return importar_varios(recoger_pdfs_en_carpeta(carpeta))


def filtrar_rutas_pdf(urls: List[str]) -> List[str]:
    """Normaliza rutas locales desde un drop de Qt."""
    rutas = []
    for url in urls:
        path = url
        if path.startswith("file:///"):
            path = path[7:]
        elif path.startswith("file://"):
            path = path[7:]
        path = os.path.normpath(path)
        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            rutas.append(path)
    return rutas
