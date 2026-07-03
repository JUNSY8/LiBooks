"""Sincronización cifrada opcional (progreso + anotaciones) vía carpeta compartida."""

import datetime
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sync_crypto import (
    SYNC_VERSION, decrypt_payload, encrypt_payload,
    make_verifier, new_salt_b64, verify_passphrase,
)
from app_settings import (
    get_setting, set_setting,
    get_sync_enabled, set_sync_enabled,
    get_sync_folder, set_sync_folder,
    get_sync_salt, set_sync_salt,
    get_sync_verifier, set_sync_verifier,
    get_sync_device_id, ensure_sync_device_id,
)

logger = logging.getLogger(__name__)

SYNC_FILENAME = "libooks-sync.enc"
_session_passphrase: Optional[str] = None


class SyncError(Exception):
    pass


def set_session_passphrase(passphrase: Optional[str]) -> None:
    global _session_passphrase
    _session_passphrase = passphrase


def get_session_passphrase() -> Optional[str]:
    return _session_passphrase


def sync_file_path() -> Optional[str]:
    folder = get_sync_folder()
    if not folder:
        return None
    return os.path.join(folder, SYNC_FILENAME)


def is_sync_configured() -> bool:
    return bool(
        get_sync_enabled()
        and get_sync_folder()
        and get_sync_salt()
        and get_sync_verifier()
    )


def setup_sync(passphrase: str, folder: str) -> None:
    salt = new_salt_b64()
    import base64
    salt_bytes = base64.urlsafe_b64decode(salt.encode("ascii"))
    verifier = make_verifier(passphrase, salt_bytes)
    set_sync_salt(salt)
    set_sync_verifier(verifier)
    set_sync_folder(folder)
    set_sync_enabled(True)
    ensure_sync_device_id()
    set_session_passphrase(passphrase)


def check_passphrase(passphrase: str) -> bool:
    salt = get_sync_salt()
    verifier = get_sync_verifier()
    if not salt or not verifier:
        return False
    return verify_passphrase(passphrase, salt, verifier)


def _dt_iso(dt) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, datetime.datetime):
        return dt.replace(microsecond=0).isoformat() + "Z"
    return str(dt)


def _parse_dt(value: Optional[str]) -> Optional[datetime.datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1]
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        return None


def export_snapshot() -> Dict[str, Any]:
    from crud import (
        obtener_libros, obtener_etiquetas_libro, brillo_libro_a_clave,
    )
    from models import Nota, Marcador, Resaltado
    from db import session

    books = []
    for libro in obtener_libros():
        if not libro.file_hash:
            continue
        notas = session.query(Nota).filter_by(id_libro=libro.id_libro).all()
        marcadores = session.query(Marcador).filter_by(id_libro=libro.id_libro).all()
        resaltados = session.query(Resaltado).filter_by(id_libro=libro.id_libro).all()
        etiquetas = [e.nombre for e in obtener_etiquetas_libro(libro.id_libro)]
        brillo = brillo_libro_a_clave(libro)
        books.append({
            "file_hash": libro.file_hash,
            "titulo": libro.titulo,
            "paginas_leidas": libro.paginas_leidas or 0,
            "ultima_lectura": _dt_iso(libro.ultima_lectura),
            "etiquetas": etiquetas,
            "brillo": brillo,
            "notas": [
                {
                    "titulo": n.titulo,
                    "contenido": n.contenido,
                    "pagina": n.pagina,
                    "fragmento": n.fragmento,
                    "rects": n.rects,
                    "fecha": _dt_iso(n.fecha_creacion),
                }
                for n in notas
            ],
            "marcadores": [
                {
                    "pagina": m.pagina,
                    "etiqueta": m.etiqueta,
                    "fecha": _dt_iso(m.fecha_creacion),
                }
                for m in marcadores
            ],
            "resaltados": [
                {
                    "pagina": h.pagina,
                    "texto": h.texto,
                    "rects": h.rects,
                    "fecha": _dt_iso(h.fecha_creacion),
                }
                for h in resaltados
            ],
        })

    return {
        "version": SYNC_VERSION,
        "device_id": ensure_sync_device_id(),
        "exported_at": _dt_iso(datetime.datetime.utcnow()),
        "books": books,
    }


def merge_snapshot(remote: Dict[str, Any]) -> Dict[str, int]:
    from crud import (
        buscar_libro_por_hash, asignar_etiquetas_libro,
        crear_nota, crear_marcador, crear_resaltado,
        actualizar_progreso_sync,
        asignar_brillo_libro_por_clave, obtener_brillo_libro,
    )
    from brillo import clave_brillo, nivel_desde_clave
    from db import session
    from models import Nota, Marcador, Resaltado

    stats = {"books": 0, "notas": 0, "marcadores": 0, "resaltados": 0, "progreso": 0}

    for entry in remote.get("books", []):
        file_hash = entry.get("file_hash")
        if not file_hash:
            continue
        libro = buscar_libro_por_hash(file_hash)
        if not libro:
            continue
        stats["books"] += 1

        remote_lectura = _parse_dt(entry.get("ultima_lectura"))
        local_lectura = libro.ultima_lectura
        remote_pag = entry.get("paginas_leidas", 0) or 0
        if remote_lectura and (not local_lectura or remote_lectura > local_lectura):
            actualizar_progreso_sync(
                libro.id_libro, remote_pag, remote_lectura
            )
            stats["progreso"] += 1

        tags = entry.get("etiquetas") or []
        if tags:
            from crud import obtener_etiquetas_libro, etiquetas_a_texto, parsear_etiquetas_texto
            actuales = set(parsear_etiquetas_texto(
                etiquetas_a_texto(obtener_etiquetas_libro(libro.id_libro))
            ))
            nuevas = sorted(actuales | set(tags))
            asignar_etiquetas_libro(libro.id_libro, nuevas)

        clave_remota = entry.get("brillo")
        if clave_remota is None and entry.get("clasificaciones"):
            clave_remota = None
        if clave_remota:
            remoto = nivel_desde_clave(clave_remota)
            local = obtener_brillo_libro(libro)
            if remoto > local:
                asignar_brillo_libro_por_clave(libro.id_libro, clave_brillo(remoto))

        for n in entry.get("notas", []):
            if _nota_existe(libro.id_libro, n):
                continue
            crear_nota(
                n.get("titulo") or "Nota",
                libro.id_libro,
                n.get("contenido"),
                pagina=n.get("pagina"),
                fragmento=n.get("fragmento"),
                rects=n.get("rects"),
            )
            stats["notas"] += 1

        for m in entry.get("marcadores", []):
            pagina = m.get("pagina")
            if pagina is None:
                continue
            existe = session.query(Marcador).filter_by(
                id_libro=libro.id_libro, pagina=pagina
            ).first()
            if existe:
                if m.get("etiqueta") and not existe.etiqueta:
                    existe.etiqueta = m.get("etiqueta")
                    session.commit()
                continue
            crear_marcador(libro.id_libro, pagina, etiqueta=m.get("etiqueta"))
            stats["marcadores"] += 1

        for h in entry.get("resaltados", []):
            if _resaltado_existe(libro.id_libro, h):
                continue
            crear_resaltado(
                libro.id_libro,
                h.get("pagina", 0),
                h.get("texto"),
                h.get("rects") or "[]",
            )
            stats["resaltados"] += 1

    return stats


def _nota_existe(id_libro: int, data: dict) -> bool:
    from db import session
    from models import Nota

    q = session.query(Nota).filter_by(
        id_libro=id_libro,
        titulo=data.get("titulo") or "Nota",
    )
    if data.get("pagina") is not None:
        q = q.filter_by(pagina=data["pagina"])
    for n in q.all():
        if (n.contenido or "") == (data.get("contenido") or ""):
            return True
        if (n.fragmento or "") == (data.get("fragmento") or "") and data.get("fragmento"):
            return True
    return False


def _resaltado_existe(id_libro: int, data: dict) -> bool:
    from db import session
    from models import Resaltado

    return session.query(Resaltado).filter_by(
        id_libro=id_libro,
        pagina=data.get("pagina", 0),
        texto=data.get("texto"),
        rects=data.get("rects"),
    ).first() is not None


def _read_remote_blob() -> Optional[bytes]:
    path = sync_file_path()
    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _write_remote_blob(data: bytes) -> None:
    path = sync_file_path()
    if not path:
        raise SyncError("sync_no_folder")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def pull(passphrase: Optional[str] = None) -> Dict[str, int]:
    phrase = passphrase or get_session_passphrase()
    if not phrase:
        raise SyncError("sync_no_passphrase")
    if not check_passphrase(phrase):
        raise SyncError("sync_bad_passphrase")
    blob = _read_remote_blob()
    if not blob:
        return {"books": 0, "notas": 0, "marcadores": 0, "resaltados": 0, "progreso": 0}
    remote = decrypt_payload(blob, phrase)
    return merge_snapshot(remote)


def push(passphrase: Optional[str] = None) -> None:
    phrase = passphrase or get_session_passphrase()
    if not phrase:
        raise SyncError("sync_no_passphrase")
    if not check_passphrase(phrase):
        raise SyncError("sync_bad_passphrase")
    salt_b64 = get_sync_salt()
    if not salt_b64:
        raise SyncError("sync_not_configured")
    import base64
    salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
    snapshot = export_snapshot()
    blob = encrypt_payload(snapshot, phrase, salt)
    _write_remote_blob(blob)


def sync_now(passphrase: Optional[str] = None) -> Tuple[Dict[str, int], bool]:
    """Descarga remoto, fusiona y sube el estado local."""
    stats = pull(passphrase)
    push(passphrase)
    return stats, True


def sync_if_enabled(passphrase: Optional[str] = None,
                     push_only: bool = False,
                     pull_only: bool = False) -> Optional[Dict[str, int]]:
    if not is_sync_configured():
        return None
    phrase = passphrase or get_session_passphrase()
    if not phrase:
        return None
    try:
        if push_only:
            push(phrase)
            return {}
        if pull_only:
            return pull(phrase)
        return sync_now(phrase)[0]
    except SyncError as e:
        logger.warning("Sync omitido: %s", e)
        return None
    except Exception as e:
        logger.exception("Error de sincronización: %s", e)
        return None


def export_to_file(dest_path: str, passphrase: str) -> None:
    salt_b64 = get_sync_salt()
    if not salt_b64:
        salt_b64 = new_salt_b64()
    import base64
    salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
    blob = encrypt_payload(export_snapshot(), passphrase, salt)
    with open(dest_path, "wb") as f:
        f.write(blob)


def import_from_file(src_path: str, passphrase: str) -> Dict[str, int]:
    with open(src_path, "rb") as f:
        blob = f.read()
    remote = decrypt_payload(blob, passphrase)
    return merge_snapshot(remote)
