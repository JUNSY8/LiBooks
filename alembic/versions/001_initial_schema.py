"""Esquema inicial normalizado de LiBooks.

Revision ID: 001
Revises:
Create Date: 2026-06-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "autor",
        sa.Column("id_autor", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id_autor"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "genero",
        sa.Column("id_genero", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id_genero"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "coleccion",
        sa.Column("id_coleccion", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id_coleccion"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "libro",
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("archivo_pdf", sa.String(), nullable=False),
        sa.Column("id_autor", sa.Integer(), nullable=True),
        sa.Column("id_genero", sa.Integer(), nullable=True),
        sa.Column("paginas_leidas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_paginas", sa.Integer(), nullable=True),
        sa.Column("fecha_agregado", sa.TIMESTAMP(), nullable=True),
        sa.Column("ultima_lectura", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["id_autor"], ["autor.id_autor"]),
        sa.ForeignKeyConstraint(["id_genero"], ["genero.id_genero"]),
        sa.PrimaryKeyConstraint("id_libro"),
        sa.UniqueConstraint("archivo_pdf"),
    )
    op.create_table(
        "libro_coleccion",
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("id_coleccion", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_coleccion"], ["coleccion.id_coleccion"]),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"]),
        sa.PrimaryKeyConstraint("id_libro", "id_coleccion"),
    )
    op.create_table(
        "marcador",
        sa.Column("id_marcador", sa.Integer(), nullable=False),
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("pagina", sa.Integer(), nullable=False),
        sa.Column("etiqueta", sa.String(), nullable=True),
        sa.Column("fecha_creacion", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"]),
        sa.PrimaryKeyConstraint("id_marcador"),
        sa.UniqueConstraint("id_libro", "pagina", name="uq_marcador_libro_pagina"),
    )
    op.create_table(
        "nota",
        sa.Column("id_nota", sa.Integer(), nullable=False),
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"]),
        sa.PrimaryKeyConstraint("id_nota"),
    )


def downgrade() -> None:
    op.drop_table("nota")
    op.drop_table("marcador")
    op.drop_table("libro_coleccion")
    op.drop_table("libro")
    op.drop_table("coleccion")
    op.drop_table("genero")
    op.drop_table("autor")
