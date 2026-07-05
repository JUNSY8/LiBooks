"""Valoracion por estrellas (1-5) para libros."""

from typing import List, Optional, Tuple

from i18n import tr

RATING_MAX = 5

_LEGACY_KEYS: Tuple[str, ...] = ("bruma", "chispa", "llama", "resplandor", "farol")

STAR_ACTIVE_RGB = (251, 191, 36)
STAR_INACTIVE_RGB = (100, 116, 139)


def normalizar_rating(nivel) -> int:
    try:
        n = int(nivel)
    except (TypeError, ValueError):
        return 0
    if n < 0:
        return 0
    if n > RATING_MAX:
        return RATING_MAX
    return n


def rating_desde_sync(valor) -> int:
    if valor is None:
        return 0
    if isinstance(valor, int):
        return normalizar_rating(valor)
    if isinstance(valor, float):
        return normalizar_rating(int(valor))
    if isinstance(valor, str):
        clave = valor.strip().lower()
        for i, key in enumerate(_LEGACY_KEYS, start=1):
            if key == clave:
                return i
        try:
            return normalizar_rating(int(clave))
        except ValueError:
            return 0
    return 0


def etiqueta_rating(nivel: int) -> str:
    n = normalizar_rating(nivel)
    if n == 0:
        return tr("rating.none")
    if n == 1:
        return tr("rating.one_star")
    return tr("rating.stars_label", count=n)


def opciones_filtro_rating() -> List[Tuple[Optional[int], str]]:
    return [
        (None, tr("library.rating_filter_all")),
        (0, tr("library.rating_filter_none")),
        *[(i, tr("rating.stars_label", count=i)) for i in range(1, RATING_MAX + 1)],
    ]