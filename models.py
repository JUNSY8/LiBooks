"""Modelos de datos (SQLAlchemy).

Esquema normalizado:
- ``Autor`` y ``Genero`` se extraen en sus propias tablas para evitar
  repetición de texto y permitir integridad referencial (3NF).
- ``libro_coleccion`` es la tabla puente de la relación N:M entre libros y
  colecciones.
- ``Nota`` y ``Marcador`` dependen de ``Libro`` (1:N) y se borran en cascada.
"""

import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    TIMESTAMP,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db import Base


class Autor(Base):
    __tablename__ = "autor"

    id_autor = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)

    libros = relationship("Libro", back_populates="autor")


class Genero(Base):
    __tablename__ = "genero"

    id_genero = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)

    libros = relationship("Libro", back_populates="genero")


class Libro(Base):
    __tablename__ = "libro"

    id_libro = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)
    archivo_pdf = Column(String, nullable=False, unique=True)
    id_autor = Column(Integer, ForeignKey("autor.id_autor"), nullable=True)
    id_genero = Column(Integer, ForeignKey("genero.id_genero"), nullable=True)

    # Progreso de lectura.
    paginas_leidas = Column(Integer, nullable=False, default=0)
    total_paginas = Column(Integer, nullable=True)

    # Metadatos de biblioteca.
    fecha_agregado = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    ultima_lectura = Column(TIMESTAMP, nullable=True)
    file_hash = Column(String(64), nullable=True, unique=True)
    # Estado funcional manual (None = calcular desde progreso).
    estado_manual = Column(String, nullable=True)
    # Valoracion por estrellas (NULL = sin valorar, 1-5).
    brillo = Column(Integer, nullable=True)
    # Columna legacy (modo privacidad retirado).
    sensible = Column(Integer, nullable=False, default=0)

    autor = relationship("Autor", back_populates="libros")
    genero = relationship("Genero", back_populates="libros")
    notas = relationship(
        "Nota", back_populates="libro", cascade="all, delete-orphan"
    )
    marcadores = relationship(
        "Marcador", back_populates="libro", cascade="all, delete-orphan"
    )
    resaltados = relationship(
        "Resaltado", back_populates="libro", cascade="all, delete-orphan"
    )
    colecciones = relationship(
        "Coleccion", secondary="libro_coleccion", back_populates="libros"
    )
    etiquetas = relationship(
        "Etiqueta", secondary="libro_etiqueta", back_populates="libros"
    )


class Nota(Base):
    __tablename__ = "nota"

    id_nota = Column(Integer, primary_key=True)
    id_libro = Column(Integer, ForeignKey("libro.id_libro"), nullable=False)
    titulo = Column(String, nullable=False)
    contenido = Column(Text)
    pagina = Column(Integer, nullable=True)
    fragmento = Column(Text, nullable=True)
    rects = Column(Text, nullable=True)
    fecha_creacion = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    libro = relationship("Libro", back_populates="notas")


class Resaltado(Base):
    """Resaltado de texto anclado a una página del PDF."""

    __tablename__ = "resaltado"

    id_resaltado = Column(Integer, primary_key=True)
    id_libro = Column(Integer, ForeignKey("libro.id_libro"), nullable=False)
    pagina = Column(Integer, nullable=False)
    texto = Column(Text, nullable=True)
    rects = Column(Text, nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    libro = relationship("Libro", back_populates="resaltados")


class Marcador(Base):
    """Marcador (bookmark) que apunta a una página concreta de un libro."""

    __tablename__ = "marcador"
    __table_args__ = (UniqueConstraint("id_libro", "pagina", name="uq_marcador_libro_pagina"),)

    id_marcador = Column(Integer, primary_key=True)
    id_libro = Column(Integer, ForeignKey("libro.id_libro"), nullable=False)
    pagina = Column(Integer, nullable=False)
    etiqueta = Column(String, nullable=True)
    fecha_creacion = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    libro = relationship("Libro", back_populates="marcadores")


# Tabla puente para la relación N:M entre Libro y Coleccion.
libro_coleccion = Table(
    "libro_coleccion",
    Base.metadata,
    Column("id_libro", Integer, ForeignKey("libro.id_libro"), primary_key=True),
    Column(
        "id_coleccion", Integer, ForeignKey("coleccion.id_coleccion"), primary_key=True
    ),
)

# Tabla puente para etiquetas libres (N:M).
libro_etiqueta = Table(
    "libro_etiqueta",
    Base.metadata,
    Column("id_libro", Integer, ForeignKey("libro.id_libro"), primary_key=True),
    Column("id_etiqueta", Integer, ForeignKey("etiqueta.id_etiqueta"), primary_key=True),
)


class Etiqueta(Base):
    """Etiqueta libre asignable a libros (p. ej. «pendiente», «favorito»)."""

    __tablename__ = "etiqueta"

    id_etiqueta = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)

    libros = relationship(
        "Libro", secondary=libro_etiqueta, back_populates="etiquetas"
    )


class Coleccion(Base):
    __tablename__ = "coleccion"

    id_coleccion = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)

    libros = relationship(
        "Libro", secondary=libro_coleccion, back_populates="colecciones"
    )
