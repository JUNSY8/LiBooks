"""Exportación de anotaciones de un libro a TXT o Markdown."""

import os
from datetime import datetime
from typing import Literal, Optional

from crud import (
    obtener_libro_por_id,
    obtener_marcadores_por_libro,
    obtener_notas_por_libro,
    obtener_resaltados_por_libro,
)
from i18n import tr


def _fmt_fecha(dt) -> str:
    if not dt:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)


def _progreso_texto(libro) -> str:
    leidas = libro.paginas_leidas or 0
    total = libro.total_paginas or 0
    if total > 0:
        pct = int(100 * leidas / total)
        return tr("export.progress_line", current=leidas, total=total, pct=pct)
    return tr("export.progress_unknown")


def exportar_anotaciones(
    id_libro: int,
    ruta_destino: str,
    formato: Literal["md", "txt"] = "md",
) -> bool:
    libro = obtener_libro_por_id(id_libro)
    if not libro:
        return False

    autor = libro.autor.nombre if libro.autor else tr("books.unknown_author")
    marcadores = obtener_marcadores_por_libro(id_libro)
    notas = obtener_notas_por_libro(id_libro)
    resaltados = obtener_resaltados_por_libro(id_libro)

    if formato == "md":
        contenido = _generar_markdown(libro, autor, marcadores, notas, resaltados)
    else:
        contenido = _generar_txt(libro, autor, marcadores, notas, resaltados)

    os.makedirs(os.path.dirname(os.path.abspath(ruta_destino)) or ".", exist_ok=True)
    with open(ruta_destino, "w", encoding="utf-8") as f:
        f.write(contenido)
    return True


def _generar_markdown(libro, autor, marcadores, notas, resaltados) -> str:
    lineas = [
        f"# {libro.titulo}",
        "",
        f"**{tr('export.author')}:** {autor}",
        f"**{tr('export.progress')}:** {_progreso_texto(libro)}",
        f"**{tr('export.exported_at')}:** {_fmt_fecha(datetime.utcnow())}",
        "",
    ]

    if marcadores:
        lineas += [f"## {tr('pdf.bookmarks')}", ""]
        for m in marcadores:
            if m.etiqueta:
                lineas.append(
                    f"- {tr('pdf.bookmark_item', name=m.etiqueta, page=m.pagina + 1)}"
                )
            else:
                lineas.append(f"- {tr('pdf.bookmark_page_only', page=m.pagina + 1)}")
        lineas.append("")

    if notas:
        lineas += [f"## {tr('pdf.notes')}", ""]
        for n in notas:
            lineas.append(f"### {n.titulo}")
            if n.pagina is not None:
                lineas.append(f"*{tr('export.page_ref', page=n.pagina + 1)}*")
            if n.fragmento:
                lineas.append(f"> {n.fragmento}")
            if n.contenido:
                lineas.append("")
                lineas.append(n.contenido)
            lineas.append("")

    if resaltados:
        lineas += [f"## {tr('pdf.highlights')}", ""]
        for h in resaltados:
            texto = (h.texto or "").replace("\n", " ")
            lineas.append(
                f"- {tr('pdf.highlight_item', page=h.pagina + 1, text=texto)}"
            )
        lineas.append("")

    if not marcadores and not notas and not resaltados:
        lineas.append(f"*{tr('export.empty')}*")

    return "\n".join(lineas)


def _generar_txt(libro, autor, marcadores, notas, resaltados) -> str:
    sep = "=" * 60
    lineas = [
        libro.titulo,
        sep,
        f"{tr('export.author')}: {autor}",
        f"{tr('export.progress')}: {_progreso_texto(libro)}",
        f"{tr('export.exported_at')}: {_fmt_fecha(datetime.utcnow())}",
        "",
    ]

    if marcadores:
        lineas += [tr("pdf.bookmarks").upper(), "-" * 40, ""]
        for m in marcadores:
            if m.etiqueta:
                lineas.append(
                    tr("pdf.bookmark_item", name=m.etiqueta, page=m.pagina + 1)
                )
            else:
                lineas.append(tr("pdf.bookmark_page_only", page=m.pagina + 1))
        lineas.append("")

    if notas:
        lineas += [tr("pdf.notes").upper(), "-" * 40, ""]
        for n in notas:
            lineas.append(n.titulo)
            if n.pagina is not None:
                lineas.append(tr("export.page_ref", page=n.pagina + 1))
            if n.fragmento:
                lineas.append(f'"{n.fragmento}"')
            if n.contenido:
                lineas.append(n.contenido)
            lineas.append("")

    if resaltados:
        lineas += [tr("pdf.highlights").upper(), "-" * 40, ""]
        for h in resaltados:
            texto = (h.texto or "").replace("\n", " ")
            lineas.append(tr("pdf.highlight_item", page=h.pagina + 1, text=texto))
        lineas.append("")

    if not marcadores and not notas and not resaltados:
        lineas.append(tr("export.empty"))

    return "\n".join(lineas)
