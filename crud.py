import datetime
import logging
import os
import shutil
from typing import List, Optional

from sqlalchemy import func, case, or_, and_, desc, asc, not_

from db import session, PDF_FOLDER
from models import (
    Libro, Nota, Autor, Genero, Coleccion, Marcador, Resaltado, Etiqueta, libro_etiqueta,
)
from rating import normalizar_rating
from pdf_meta import extraer_metadatos, hash_archivo
from covers import generar_portada, eliminar_portada
from reading_status import (
    obtener_estado_efectivo,
    normalizar_estado_manual,
    sincronizar_estado_tras_progreso,
)

logger = logging.getLogger(__name__)


def ruta_absoluta_libro(libro: Libro) -> Optional[str]:
    """Ruta en disco del PDF de un libro, o None si no existe."""
    if getattr(libro, "ruta_archivo", None):
        return libro.ruta_archivo
    if libro.archivo_pdf:
        ruta = os.path.join(PDF_FOLDER, libro.archivo_pdf)
        return ruta if os.path.exists(ruta) else None
    return None


def buscar_libro_por_hash(file_hash: str):
    if not file_hash:
        return None
    return session.query(Libro).filter_by(file_hash=file_hash).first()


def es_duplicado(ruta_pdf: str):
    """Devuelve el libro existente si el PDF ya está en la biblioteca."""
    h = hash_archivo(ruta_pdf)
    if not h:
        return None
    return buscar_libro_por_hash(h)


def obtener_libro_continuar_lectura():
    """Libro leído más recientemente con progreso guardado."""
    libros = (
        session.query(Libro)
        .filter(Libro.paginas_leidas > 0, Libro.ultima_lectura.isnot(None))
        .order_by(Libro.ultima_lectura.desc())
        .all()
    )
    return libros[0] if libros else None


def _ruta_pdf_unica(nombre_archivo: str) -> str:
    """Devuelve una ruta destino en PDF_FOLDER que no colisione con otra ya
    existente, añadiendo un sufijo numérico si es necesario."""
    destino = os.path.join(PDF_FOLDER, nombre_archivo)
    if not os.path.exists(destino):
        return destino

    base, ext = os.path.splitext(nombre_archivo)
    contador = 1
    while True:
        candidato = os.path.join(PDF_FOLDER, f"{base} ({contador}){ext}")
        if not os.path.exists(candidato):
            return candidato
        contador += 1


def _contar_paginas(ruta_pdf: str):
    """Cuenta las páginas de un PDF; devuelve None si no se puede leer."""
    try:
        import fitz

        with fitz.open(ruta_pdf) as doc:
            return doc.page_count
    except Exception as e:
        logger.warning("No se pudieron contar las páginas de %s: %s", ruta_pdf, e)
        return None



def buscar_o_crear_autor(nombre_autor):
    # Primero buscamos una coincidencia exacta
    autor = session.query(Autor).filter(
        func.lower(Autor.nombre) == func.lower(nombre_autor)
    ).first()
    
    # Si no hay coincidencia exacta, buscamos una coincidencia parcial
    if not autor:
        autor = session.query(Autor).filter(
            func.lower(Autor.nombre).contains(func.lower(nombre_autor))
        ).first()
    
    # Si aún no encontramos un autor, lo creamos
    if not autor and nombre_autor.strip():
        autor = Autor(nombre=nombre_autor.strip())
        session.add(autor)
        session.commit()
    
    return autor

def buscar_o_crear_genero(nombre_genero):
    if not nombre_genero or not nombre_genero.strip():
        return None
        
    nombre_genero = nombre_genero.strip()
    
    # Primero buscamos una coincidencia exacta
    genero = session.query(Genero).filter(
        func.lower(Genero.nombre) == func.lower(nombre_genero)
    ).first()
    
    # Si no hay coincidencia exacta, buscamos una coincidencia parcial
    if not genero:
        genero = session.query(Genero).filter(
            func.lower(Genero.nombre).contains(func.lower(nombre_genero))
        ).first()
    
    # Si aún no encontramos un género, lo creamos
    if not genero:
        genero = Genero(nombre=nombre_genero)
        session.add(genero)
        session.commit()
    # Si encontramos un género similar pero no exacto, actualizamos el nombre
    elif genero.nombre.lower() != nombre_genero.lower():
        genero.nombre = nombre_genero
        session.commit()
    
    return genero

def crear_libro_pdf(ruta_pdf_original, titulo=None, nombre_autor=None, nombre_genero=None, fecha_lectura=None, paginas_leidas=0):
    destino = None
    try:
        if es_duplicado(ruta_pdf_original):
            return None

        file_hash = hash_archivo(ruta_pdf_original)
        meta = extraer_metadatos(ruta_pdf_original)

        nombre_archivo = os.path.basename(ruta_pdf_original)

        if not titulo or not titulo.strip():
            titulo = meta.get("titulo") or os.path.splitext(nombre_archivo)[0]
        if not nombre_autor or not nombre_autor.strip():
            nombre_autor = meta.get("autor") or None

        destino = _ruta_pdf_unica(nombre_archivo)
        shutil.copy(ruta_pdf_original, destino)
        nombre_guardado = os.path.basename(destino)

        id_autor = None
        if nombre_autor:
            autor = buscar_o_crear_autor(nombre_autor)
            id_autor = autor.id_autor

        id_genero = None
        if nombre_genero:
            genero = buscar_o_crear_genero(nombre_genero)
            id_genero = genero.id_genero

        nuevo_libro = Libro(
            titulo=titulo.strip(),
            archivo_pdf=nombre_guardado,
            id_autor=id_autor,
            id_genero=id_genero,
            paginas_leidas=paginas_leidas,
            total_paginas=_contar_paginas(destino),
            file_hash=file_hash,
        )
        session.add(nuevo_libro)
        session.commit()
        generar_portada(destino, nuevo_libro.id_libro)
        return nuevo_libro
    except Exception as e:
        logger.exception("Error al crear libro: %s", e)
        session.rollback()
        if destino and os.path.exists(destino):
            os.remove(destino)
        return None

def obtener_libros() -> List[Libro]:
    """Obtiene todos los libros de la base de datos"""
    return session.query(Libro).all()


def obtener_libro_por_id(id_libro: int) -> Optional[Libro]:
    return session.query(Libro).filter_by(id_libro=id_libro).first()

def obtener_libros_por_ids(ids_libros: List[int]) -> List[Libro]:
    """
    Obtiene una lista de libros por sus IDs
    
    Args:
        ids_libros: Lista de IDs de libros a buscar
        
    Returns:
        List[Libro]: Lista de libros encontrados
    """
    if not ids_libros:
        return []
        
    return session.query(Libro).filter(Libro.id_libro.in_(ids_libros)).all()


def actualizar_libro(id_libro, titulo=None, nombre_autor=None, nombre_genero=None, fecha_lectura=None, paginas_leidas=None, estado_manual=...):
    """Actualiza la información de un libro"""
    libro = session.query(Libro).filter_by(id_libro=id_libro).first()
    if libro:
        # Actualizar título si se proporciona
        if titulo is not None:
            libro.titulo = titulo

        # Actualizar autor si se proporciona
        if nombre_autor is not None:
            autor = buscar_o_crear_autor(nombre_autor)
            libro.id_autor = autor.id_autor

        # Actualizar género si se proporciona
        if nombre_genero is not None:
            genero = buscar_o_crear_genero(nombre_genero)
            libro.id_genero = genero.id_genero

        # Actualizar otros campos
        if fecha_lectura is not None:
            libro.fecha_lectura = fecha_lectura
        if paginas_leidas is not None:
            libro.paginas_leidas = paginas_leidas
        if estado_manual is not ...:
            libro.estado_manual = normalizar_estado_manual(estado_manual)
            sincronizar_estado_tras_progreso(libro)

        session.commit()
        return libro
    return None



def buscar_libro_por_nombre(nombre_archivo_pdf):
    return session.query(Libro).filter(Libro.archivo_pdf.ilike(f"%{nombre_archivo_pdf}%")).first()



def crear_nota(titulo, id_libro, contenido, pagina=None, fragmento=None, rects=None):
    nueva_nota = Nota(
        titulo=titulo,
        id_libro=id_libro,
        contenido=contenido,
        pagina=pagina,
        fragmento=fragmento,
        rects=rects,
    )
    session.add(nueva_nota)
    session.commit()
    return nueva_nota

def obtener_notas():
    return session.query(Nota).all()

def obtener_notas_por_libro(id_libro):
    """Obtiene todas las notas de un libro específico"""
    return (
        session.query(Nota)
        .filter_by(id_libro=id_libro)
        .order_by(Nota.fecha_creacion.desc())
        .all()
    )

def obtener_nota_por_id(id_nota):
    """Obtiene una nota por su ID"""
    return session.query(Nota).filter_by(id_nota=id_nota).first()

def actualizar_nota(id_nota, nuevo_titulo=None, nuevo_contenido=None,
                    pagina=None, fragmento=None, rects=None):
    nota = session.query(Nota).filter_by(id_nota=id_nota).first()
    if nota:
        if nuevo_titulo is not None:
            nota.titulo = nuevo_titulo
        if nuevo_contenido is not None:
            nota.contenido = nuevo_contenido
        if pagina is not None:
            nota.pagina = pagina
        if fragmento is not None:
            nota.fragmento = fragmento
        if rects is not None:
            nota.rects = rects
        session.commit()
        return nota
    return None

def eliminar_nota(id_nota):
    nota = session.query(Nota).filter_by(id_nota=id_nota).first()
    if nota:
        session.delete(nota)
        session.commit()
        return True
    return False


# ── Resaltados ────────────────────────────────────────────────────────

def crear_resaltado(id_libro, pagina, texto, rects):
    try:
        resaltado = Resaltado(
            id_libro=id_libro,
            pagina=pagina,
            texto=texto,
            rects=rects,
        )
        session.add(resaltado)
        session.commit()
        return resaltado
    except Exception as e:
        logger.exception("Error al crear resaltado: %s", e)
        session.rollback()
        return None


def obtener_resaltados_por_libro(id_libro):
    try:
        return (
            session.query(Resaltado)
            .filter_by(id_libro=id_libro)
            .order_by(Resaltado.pagina.asc(), Resaltado.fecha_creacion.asc())
            .all()
        )
    except Exception as e:
        logger.exception("Error al obtener resaltados: %s", e)
        return []


def obtener_resaltados_pagina(id_libro, pagina):
    return (
        session.query(Resaltado)
        .filter_by(id_libro=id_libro, pagina=pagina)
        .all()
    )


def eliminar_resaltado(id_resaltado):
    try:
        r = session.query(Resaltado).filter_by(id_resaltado=id_resaltado).first()
        if r:
            session.delete(r)
            session.commit()
            return True
        return False
    except Exception as e:
        logger.exception("Error al eliminar resaltado: %s", e)
        session.rollback()
        return False

def actualizar_paginas_leidas(id_libro, pagina_actual):
    """Actualiza la página actual del libro y la fecha de última lectura"""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if libro:
            libro.paginas_leidas = pagina_actual
            libro.ultima_lectura = datetime.datetime.utcnow()
            sincronizar_estado_tras_progreso(libro)
            session.commit()
            return True
        return False
    except Exception as e:
        logger.exception("Error al actualizar páginas leídas: %s", e)
        session.rollback()
        return False


def actualizar_progreso_sync(id_libro, paginas_leidas, ultima_lectura):
    """Actualiza progreso desde sync sin sobrescribir la fecha remota."""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if not libro:
            return False
        libro.paginas_leidas = paginas_leidas or 0
        libro.ultima_lectura = ultima_lectura
        sincronizar_estado_tras_progreso(libro)
        session.commit()
        return True
    except Exception as e:
        logger.exception("Error al aplicar progreso sync: %s", e)
        session.rollback()
        return False


def crear_marcador(id_libro, pagina, etiqueta=None):
    """Crea un marcador para una página del libro. Si ya existe uno en esa
    página, actualiza la etiqueta si se proporciona."""
    try:
        existente = session.query(Marcador).filter_by(
            id_libro=id_libro, pagina=pagina
        ).first()
        if existente:
            if etiqueta is not None:
                existente.etiqueta = etiqueta.strip() or None
                session.commit()
            return existente

        marcador = Marcador(
            id_libro=id_libro,
            pagina=pagina,
            etiqueta=etiqueta.strip() if etiqueta else None,
        )
        session.add(marcador)
        session.commit()
        return marcador
    except Exception as e:
        logger.exception("Error al crear marcador: %s", e)
        session.rollback()
        return None


def actualizar_marcador(id_marcador, etiqueta=None):
    """Actualiza el nombre (etiqueta) de un marcador."""
    try:
        marcador = session.query(Marcador).filter_by(id_marcador=id_marcador).first()
        if not marcador:
            return False
        marcador.etiqueta = etiqueta.strip() if etiqueta else None
        session.commit()
        return True
    except Exception as e:
        logger.exception("Error al actualizar marcador: %s", e)
        session.rollback()
        return False


def obtener_marcadores_por_libro(id_libro):
    """Devuelve los marcadores de un libro ordenados por página."""
    try:
        return (
            session.query(Marcador)
            .filter_by(id_libro=id_libro)
            .order_by(Marcador.pagina.asc())
            .all()
        )
    except Exception as e:
        logger.exception("Error al obtener marcadores: %s", e)
        return []


def eliminar_marcador(id_marcador):
    """Elimina un marcador por su ID."""
    try:
        marcador = session.query(Marcador).filter_by(id_marcador=id_marcador).first()
        if marcador:
            session.delete(marcador)
            session.commit()
            return True
        return False
    except Exception as e:
        logger.exception("Error al eliminar marcador: %s", e)
        session.rollback()
        return False

def obtener_paginas_leidas(id_libro):
    """Obtiene la última página leída del libro"""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if libro:
            return libro.paginas_leidas
        return 0
    except Exception as e:
        logger.exception("Error al obtener páginas leídas: %s", e)
        return 0

def crear_coleccion(nombre):
    """Crea una nueva colección"""
    try:
        # Verificar si ya existe una colección con el mismo nombre
        coleccion_existente = session.query(Coleccion).filter_by(nombre=nombre).first()
        if coleccion_existente:
            logger.info("Ya existe una colección con el nombre: %s", nombre)
            return False

        # Crear la nueva colección
        nueva_coleccion = Coleccion(nombre=nombre)
        session.add(nueva_coleccion)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error al crear la colección: %s", e)
        return False

def obtener_colecciones():
    """Obtiene todas las colecciones"""
    try:
        return session.query(Coleccion).all()
    except Exception as e:
        logger.exception("Error al obtener las colecciones: %s", e)
        return []

def eliminar_coleccion(id_coleccion):
    """Elimina una colección por su ID"""
    try:
        coleccion = session.query(Coleccion).get(id_coleccion)
        if coleccion:
            # Eliminar las relaciones en la tabla puente primero
            coleccion.libros = []
            session.commit()
            
            # Luego eliminar la colección
            session.delete(coleccion)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.exception("Error al eliminar la colección: %s", e)
        return False

def eliminar_libro(id_libro):
    """
    Elimina un libro de la base de datos junto con todas sus referencias.
    
    Args:
        id_libro (int): ID del libro a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        # Obtener el libro
        libro = session.query(Libro).get(id_libro)
        if not libro:
            return False
        
        # Obtener las relaciones por separado
        notas = session.query(Nota).filter_by(id_libro=id_libro).all()
        colecciones = session.query(Coleccion).filter(Coleccion.libros.any(id_libro=id_libro)).all()
        
        # 1. Eliminar el archivo PDF físico si existe
        eliminar_portada(id_libro)
        if libro.archivo_pdf:
            ruta_pdf = os.path.join(PDF_FOLDER, libro.archivo_pdf)
            if os.path.exists(ruta_pdf):
                try:
                    os.remove(ruta_pdf)
                except Exception as e:
                    logger.warning("No se pudo eliminar el archivo PDF: %s", e)
        
        # 2. Eliminar todas las notas asociadas al libro
        for nota in notas:
            session.delete(nota)
        
        # 3. Eliminar las relaciones con las colecciones
        for coleccion in colecciones:
            libro.colecciones.remove(coleccion)
        
        # 4. Guardar referencias a autor y género antes de eliminar el libro
        autor_id = libro.id_autor
        genero_id = libro.id_genero
        
        # 5. Eliminar el libro
        session.delete(libro)
        session.commit()
        
        # 6. Verificar si el autor y el género quedan sin referencias y eliminarlos si es necesario
        if autor_id:
            # Verificar si el autor tiene más libros
            libros_del_autor = session.query(Libro).filter_by(id_autor=autor_id).count()
            if libros_del_autor == 0:
                autor = session.query(Autor).get(autor_id)
                if autor:
                    session.delete(autor)
                    session.commit()
        
        if genero_id:
            # Verificar si el género tiene más libros
            libros_del_genero = session.query(Libro).filter_by(id_genero=genero_id).count()
            if libros_del_genero == 0:
                genero = session.query(Genero).get(genero_id)
                if genero:
                    session.delete(genero)
                    session.commit()
        
        return True
        
    except Exception as e:
        session.rollback()
        logger.exception("Error al eliminar el libro: %s", e)
        return False

def agregar_libro_a_coleccion(id_coleccion, id_libro):
    """Agrega un libro a una colección"""
    try:
        coleccion = session.query(Coleccion).get(id_coleccion)
        libro = session.query(Libro).get(id_libro)
        
        if not coleccion or not libro:
            logger.warning("Colección o libro no encontrado")
            return False
            
        if libro in coleccion.libros:
            logger.info("El libro ya está en la colección")
            return False
            
        coleccion.libros.append(libro)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error al agregar libro a la colección: %s", e)
        return False

def quitar_libro_de_coleccion(id_coleccion, id_libro):
    """Quita un libro de una colección"""
    try:
        coleccion = session.query(Coleccion).get(id_coleccion)
        libro = session.query(Libro).get(id_libro)
        
        if not coleccion or not libro:
            logger.warning("Colección o libro no encontrado")
            return False
            
        if libro not in coleccion.libros:
            logger.info("El libro no está en la colección")
            return False
            
        coleccion.libros.remove(libro)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error al quitar libro de la colección: %s", e)
        return False

def actualizar_nombre_coleccion(id_coleccion, nuevo_nombre):
    """Actualiza el nombre de una colección"""
    try:
        coleccion = session.query(Coleccion).get(id_coleccion)
        if coleccion:
            # Verificar si ya existe otra colección con el mismo nombre
            existe = session.query(Coleccion).filter(
                Coleccion.nombre == nuevo_nombre,
                Coleccion.id_coleccion != id_coleccion
            ).first()
            
            if existe:
                logger.info("Ya existe otra colección con ese nombre")
                return False
                
            coleccion.nombre = nuevo_nombre
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.exception("Error al actualizar el nombre de la colección: %s", e)
        return False


def actualizar_coleccion(id_coleccion, nombre, libros_ids):
    """Actualiza el nombre y los libros de una colección."""
    try:
        coleccion = session.query(Coleccion).get(id_coleccion)
        if not coleccion:
            return False

        existe = session.query(Coleccion).filter(
            Coleccion.nombre == nombre,
            Coleccion.id_coleccion != id_coleccion,
        ).first()
        if existe:
            logger.info("Ya existe otra colección con ese nombre")
            return False

        ids_unicos = list(dict.fromkeys(libros_ids))
        libros = session.query(Libro).filter(Libro.id_libro.in_(ids_unicos)).all()
        if not ids_unicos or len(libros) != len(ids_unicos):
            return False

        coleccion.nombre = nombre
        coleccion.libros = libros
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.exception("Error al actualizar la colección: %s", e)
        return False

def obtener_coleccion_por_id(id_coleccion):
    """Obtiene una colección por su ID"""
    try:
        return session.query(Coleccion).get(id_coleccion)
    except Exception as e:
        logger.exception("Error al obtener la colección: %s", e)
        return None

def obtener_libros_en_coleccion(id_coleccion):
    """Obtiene todos los libros que pertenecen a una colección específica"""
    try:
        from models import libro_coleccion, Libro

        libros = session.query(Libro).join(
            libro_coleccion,
            Libro.id_libro == libro_coleccion.c.id_libro
        ).filter(
            libro_coleccion.c.id_coleccion == id_coleccion
        ).all()

        return libros
    except Exception as e:
        logger.exception("Error al obtener libros de la colección: %s", e)
        return []


# ── Consulta de biblioteca (ordenar / filtrar) ───────────────────────────

_SORT_KEYS = {
    "title_asc": Libro.titulo.asc(),
    "title_desc": Libro.titulo.desc(),
    "author_asc": Autor.nombre.asc().nullslast(),
    "date_added_desc": Libro.fecha_agregado.desc().nullslast(),
    "date_added_asc": Libro.fecha_agregado.asc().nullslast(),
    "last_read_desc": Libro.ultima_lectura.desc().nullslast(),
    "progress_desc": desc(
        case((Libro.total_paginas > 0, Libro.paginas_leidas * 1.0 / Libro.total_paginas), else_=0)
    ),
    "progress_asc": asc(
        case((Libro.total_paginas > 0, Libro.paginas_leidas * 1.0 / Libro.total_paginas), else_=0)
    ),
}


def _auto_completed_cond():
    return and_(
        Libro.total_paginas.isnot(None),
        Libro.total_paginas > 0,
        Libro.paginas_leidas >= Libro.total_paginas,
    )


def _auto_unread_cond():
    return or_(Libro.paginas_leidas.is_(None), Libro.paginas_leidas == 0)


def _estado_efectivo_expr():
    """Expresión SQL que replica obtener_estado_efectivo()."""
    completed = _auto_completed_cond()
    unread = _auto_unread_cond()
    manual_mantiene = and_(
        Libro.estado_manual.isnot(None),
        or_(
            Libro.estado_manual.notin_(("unread", "reading")),
            not_(completed),
        ),
    )
    return case(
        (and_(Libro.estado_manual.isnot(None), manual_mantiene), Libro.estado_manual),
        (unread, "unread"),
        (completed, "completed"),
        else_="reading",
    )


def consultar_biblioteca(
    filtro_texto: Optional[str] = None,
    orden: str = "title_asc",
    estado: str = "all",
    id_etiqueta: Optional[int] = None,
    id_coleccion: Optional[int] = None,
    rating: Optional[int] = None,
    solo_con_archivo: bool = True,
) -> List[Libro]:
    """Lista libros con búsqueda, filtros y ordenación."""
    q = session.query(Libro).outerjoin(Autor).outerjoin(Genero)

    if id_coleccion:
        from models import libro_coleccion
        q = q.join(
            libro_coleccion, Libro.id_libro == libro_coleccion.c.id_libro
        ).filter(libro_coleccion.c.id_coleccion == id_coleccion)

    if id_etiqueta:
        q = q.join(libro_etiqueta, Libro.id_libro == libro_etiqueta.c.id_libro).filter(
            libro_etiqueta.c.id_etiqueta == id_etiqueta
        )

    if rating is not None:
        if rating == 0:
            q = q.filter(or_(Libro.brillo.is_(None), Libro.brillo == 0))
        else:
            q = q.filter(Libro.brillo == rating)

    if filtro_texto and filtro_texto.strip():
        f = f"%{filtro_texto.strip().lower()}%"
        q = q.filter(
            or_(
                func.lower(Libro.titulo).like(f),
                func.lower(Autor.nombre).like(f),
                func.lower(Genero.nombre).like(f),
                Libro.etiquetas.any(func.lower(Etiqueta.nombre).like(f)),
            )
        )

    if estado and estado != "all":
        q = q.filter(_estado_efectivo_expr() == estado)

    order_col = _SORT_KEYS.get(orden, _SORT_KEYS["title_asc"])
    libros = q.order_by(order_col, Libro.titulo.asc()).all()

    if solo_con_archivo:
        libros = [lb for lb in libros if ruta_absoluta_libro(lb)]
    return libros


# ── Etiquetas libres ─────────────────────────────────────────────────────

def buscar_o_crear_etiqueta(nombre: str) -> Optional[Etiqueta]:
    nombre = (nombre or "").strip()
    if not nombre:
        return None
    existente = session.query(Etiqueta).filter(
        func.lower(Etiqueta.nombre) == func.lower(nombre)
    ).first()
    if existente:
        return existente
    etiqueta = Etiqueta(nombre=nombre)
    session.add(etiqueta)
    session.commit()
    return etiqueta


def obtener_etiquetas() -> List[Etiqueta]:
    return session.query(Etiqueta).order_by(Etiqueta.nombre.asc()).all()


def obtener_generos() -> List[Genero]:
    return session.query(Genero).order_by(Genero.nombre.asc()).all()


def obtener_etiquetas_libro(id_libro: int) -> List[Etiqueta]:
    libro = session.query(Libro).filter_by(id_libro=id_libro).first()
    return list(libro.etiquetas) if libro else []


def asignar_etiquetas_libro(id_libro: int, nombres: List[str]) -> bool:
    """Reemplaza las etiquetas de un libro por la lista indicada."""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if not libro:
            return False
        etiquetas = []
        for nombre in nombres:
            nombre = nombre.strip()
            if not nombre:
                continue
            et = buscar_o_crear_etiqueta(nombre)
            if et:
                etiquetas.append(et)
        libro.etiquetas = etiquetas
        session.commit()
        return True
    except Exception as e:
        logger.exception("Error al asignar etiquetas: %s", e)
        session.rollback()
        return False


def parsear_etiquetas_texto(texto: str) -> List[str]:
    """Convierte «tag1, tag2» en lista de nombres."""
    if not texto:
        return []
    partes = []
    for parte in texto.replace(";", ",").split(","):
        p = parte.strip()
        if p and p not in partes:
            partes.append(p)
    return partes


def etiquetas_a_texto(etiquetas: List[Etiqueta]) -> str:
    return ", ".join(e.nombre for e in sorted(etiquetas, key=lambda x: x.nombre.lower()))


# ── Valoración por estrellas (columna libro.brillo, 1–5) ───────────────────

def obtener_rating_libro(libro: Libro) -> int:
    return normalizar_rating(getattr(libro, "brillo", None) or 0)


def asignar_rating_libro(id_libro: int, nivel: int) -> bool:
    """Asigna valoración 0-5 a un libro (0 = quitar)."""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if not libro:
            return False
        n = normalizar_rating(nivel)
        libro.brillo = n if n > 0 else None
        session.commit()
        return True
    except Exception as e:
        logger.exception("Error al asignar valoracion: %s", e)
        session.rollback()
        return False


def rating_libro_para_sync(libro: Libro) -> Optional[int]:
    n = obtener_rating_libro(libro)
    return n if n > 0 else None


# ── Estadísticas de lectura ──────────────────────────────────────────────

def obtener_estadisticas_lectura() -> dict:
    """Métricas agregadas de la biblioteca."""
    ahora = datetime.datetime.utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    libros = session.query(Libro).all()
    libros = [lb for lb in libros if ruta_absoluta_libro(lb)]

    total = len(libros)
    en_progreso = 0
    completados = 0
    sin_leer = 0
    paginas_totales = 0
    activos_mes = 0

    for lb in libros:
        if obtener_estado_efectivo(lb) == "unread":
            sin_leer += 1
        elif obtener_estado_efectivo(lb) == "completed":
            completados += 1
        elif obtener_estado_efectivo(lb) == "reading":
            en_progreso += 1

        leidas = lb.paginas_leidas or 0
        paginas_totales += leidas

        if lb.ultima_lectura and lb.ultima_lectura >= inicio_mes:
            activos_mes += 1

    recientes = (
        session.query(Libro)
        .filter(Libro.ultima_lectura.isnot(None))
        .order_by(Libro.ultima_lectura.desc())
        .limit(5)
        .all()
    )
    recientes = [lb for lb in recientes if ruta_absoluta_libro(lb)][:5]

    return {
        "total_libros": total,
        "en_progreso": en_progreso,
        "completados": completados,
        "sin_leer": sin_leer,
        "paginas_leidas": paginas_totales,
        "activos_mes": activos_mes,
        "recientes": recientes,
    }

