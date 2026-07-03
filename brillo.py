"""Brillo bibliografico: escala fija de importancia en la biblioteca LiBooks."""

from typing import List, Optional, Tuple

from i18n import tr

BRILLO_KEYS: Tuple[str, ...] = ("bruma", "chispa", "llama", "resplandor", "farol")
BRILLO_MAX = len(BRILLO_KEYS)

BRILLO_DOT_RGB = (
    (125, 211, 252),
    (96, 165, 250),
    (74, 222, 169),
    (250, 204, 21),
    (251, 191, 36),
)
BRILLO_DOT_INACTIVE_RGB = (148, 163, 184)


def normalizar_brillo(nivel) -> int:
    try:
        n = int(nivel)
    except (TypeError, ValueError):
        return 0
    if n < 0:
        return 0
    if n > BRILLO_MAX:
        return BRILLO_MAX
    return n


def clave_brillo(nivel: int) -> Optional[str]:
    n = normalizar_brillo(nivel)
    if n == 0:
        return None
    return BRILLO_KEYS[n - 1]


def nivel_desde_clave(clave: Optional[str]) -> int:
    if not clave:
        return 0
    clave = clave.strip().lower()
    for i, key in enumerate(BRILLO_KEYS, start=1):
        if key == clave:
            return i
    return 0


def nombre_brillo(nivel: int) -> str:
    n = normalizar_brillo(nivel)
    if n == 0:
        return tr("brillo.none")
    return tr(f"brillo.level.{BRILLO_KEYS[n - 1]}")


def descripcion_brillo(nivel: int) -> str:
    n = normalizar_brillo(nivel)
    if n == 0:
        return tr("brillo.none_hint")
    return tr(f"brillo.desc.{BRILLO_KEYS[n - 1]}")


def opciones_filtro_brillo() -> List[Tuple[Optional[int], str]]:
    return [
        (None, tr("library.brillo_filter_all")),
        (0, tr("library.brillo_filter_none")),
        *[(i, nombre_brillo(i)) for i in range(1, BRILLO_MAX + 1)],
    ]


def brillo_dot_object_name(nivel: int, activo: bool) -> str:
    n = normalizar_brillo(nivel)
    if not activo or n == 0:
        return "brilloDotInactive"
    return f"brilloDotActive{n}"