"""Estados funcionales de lectura (tambien disponibles como etiquetas)."""

from typing import List, Optional, Tuple

READING_STATUSES: Tuple[str, ...] = (
    "unread",
    "reading",
    "completed",
    "paused",
    "abandoned",
)

_MANUAL_CLEAR_ON_COMPLETE = frozenset({"unread", "reading"})


def calcular_estado_automatico(
    paginas_leidas: Optional[int],
    total_paginas: Optional[int],
) -> str:
    leidas = paginas_leidas or 0
    total = total_paginas or 0
    if leidas == 0:
        return "unread"
    if total > 0 and leidas >= total:
        return "completed"
    return "reading"


def obtener_estado_efectivo(libro) -> str:
    auto = calcular_estado_automatico(libro.paginas_leidas, libro.total_paginas)
    manual = getattr(libro, "estado_manual", None)
    if manual:
        if auto == "completed" and manual in _MANUAL_CLEAR_ON_COMPLETE:
            return "completed"
        return manual
    return auto


def normalizar_estado_manual(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    valor = str(valor).strip().lower()
    if not valor or valor == "auto":
        return None
    if valor in READING_STATUSES:
        return valor
    return None


def sincronizar_estado_tras_progreso(libro) -> None:
    if not getattr(libro, "estado_manual", None):
        return
    auto = calcular_estado_automatico(libro.paginas_leidas, libro.total_paginas)
    if auto == "completed" and libro.estado_manual in _MANUAL_CLEAR_ON_COMPLETE:
        libro.estado_manual = None


def _status_labels() -> dict:
    from i18n import tr

    return {key: tr(f"reading_status.{key}") for key in READING_STATUSES}


def etiqueta_de_estado(key: str) -> str:
    from i18n import tr

    return tr(f"reading_status.{key}")


def resolver_estado_desde_etiqueta(nombre: str) -> Optional[str]:
    nombre = (nombre or "").strip().lower()
    if not nombre:
        return None
    for key, label in _status_labels().items():
        if nombre == label.lower():
            return key
    return None


def es_etiqueta_de_estado(nombre: str) -> bool:
    return resolver_estado_desde_etiqueta(nombre) is not None


def etiquetas_opciones_estado() -> List[str]:
    return [etiqueta_de_estado(key) for key in READING_STATUSES]


def separar_etiquetas_y_estado(nombres: List[str]) -> Tuple[Optional[str], List[str]]:
    estado = None
    otras: List[str] = []
    vistos = set()
    for nombre in nombres:
        nombre = (nombre or "").strip()
        if not nombre:
            continue
        key = resolver_estado_desde_etiqueta(nombre)
        if key:
            estado = key
            continue
        lower = nombre.lower()
        if lower not in vistos:
            vistos.add(lower)
            otras.append(nombre)
    return estado, otras


def etiquetas_personalizadas_libro(libro) -> List[str]:
    etiquetas = getattr(libro, "etiquetas", None) or []
    return sorted(
        [e.nombre for e in etiquetas if not es_etiqueta_de_estado(e.nombre)],
        key=str.lower,
    )


def construir_etiquetas_guardado(
    estado_manual: Optional[str],
    etiquetas_libres: List[str],
) -> List[str]:
    nombres: List[str] = []
    if estado_manual:
        nombres.append(etiqueta_de_estado(estado_manual))
    vistos = {n.lower() for n in nombres}
    for nombre in etiquetas_libres:
        nombre = (nombre or "").strip()
        if not nombre or es_etiqueta_de_estado(nombre):
            continue
        lower = nombre.lower()
        if lower not in vistos:
            vistos.add(lower)
            nombres.append(nombre)
    return nombres
