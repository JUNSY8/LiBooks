import datetime
import logging
import os
import shutil
from typing import List

from sqlalchemy import func

from db import session, PDF_FOLDER
from models import Libro, Nota, Autor, Genero, Coleccion, Marcador

logger = logging.getLogger(__name__)


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
        # Obtener el nombre del archivo original
        nombre_archivo = os.path.basename(ruta_pdf_original)

        # Si no se proporciona un título, usar el nombre del archivo sin extensión
        if not titulo:
            titulo = os.path.splitext(nombre_archivo)[0]

        # Copiar el archivo al directorio de libros evitando colisiones de nombre
        destino = _ruta_pdf_unica(nombre_archivo)
        shutil.copy(ruta_pdf_original, destino)
        nombre_guardado = os.path.basename(destino)

        # Buscar o crear autor y género si se proporcionan
        id_autor = None
        if nombre_autor:
            autor = buscar_o_crear_autor(nombre_autor)
            id_autor = autor.id_autor

        id_genero = None
        if nombre_genero:
            genero = buscar_o_crear_genero(nombre_genero)
            id_genero = genero.id_genero

        # Crear el nuevo libro
        nuevo_libro = Libro(
            titulo=titulo,
            archivo_pdf=nombre_guardado,
            id_autor=id_autor,
            id_genero=id_genero,
            paginas_leidas=paginas_leidas,
            total_paginas=_contar_paginas(destino),
        )
        session.add(nuevo_libro)
        session.commit()
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


def actualizar_libro(id_libro, titulo=None, nombre_autor=None, nombre_genero=None, fecha_lectura=None, paginas_leidas=None):
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

        session.commit()
        return libro
    return None



def buscar_libro_por_nombre(nombre_archivo_pdf):
    return session.query(Libro).filter(Libro.archivo_pdf.ilike(f"%{nombre_archivo_pdf}%")).first()



def crear_nota(titulo, id_libro, contenido):
    nueva_nota = Nota(
        titulo=titulo,
        id_libro=id_libro,
        contenido=contenido
    )
    session.add(nueva_nota)
    session.commit()
    return nueva_nota

def obtener_notas():
    return session.query(Nota).all()

def obtener_notas_por_libro(id_libro):
    """Obtiene todas las notas de un libro específico"""
    return session.query(Nota).filter_by(id_libro=id_libro).order_by(Nota.fecha_creacion.desc()).all()

def obtener_nota_por_id(id_nota):
    """Obtiene una nota por su ID"""
    return session.query(Nota).filter_by(id_nota=id_nota).first()

def actualizar_nota(id_nota, nuevo_titulo=None, nuevo_contenido=None):
    nota = session.query(Nota).filter_by(id_nota=id_nota).first()
    if nota:
        if nuevo_titulo:
            nota.titulo = nuevo_titulo
        if nuevo_contenido:
            nota.contenido = nuevo_contenido
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

def actualizar_paginas_leidas(id_libro, pagina_actual):
    """Actualiza la página actual del libro y la fecha de última lectura"""
    try:
        libro = session.query(Libro).filter_by(id_libro=id_libro).first()
        if libro:
            libro.paginas_leidas = pagina_actual
            libro.ultima_lectura = datetime.datetime.utcnow()
            session.commit()
            return True
        return False
    except Exception as e:
        logger.exception("Error al actualizar páginas leídas: %s", e)
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
