"""Etiquetas libres para libros.

Revision ID: 004
Revises: 003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "etiqueta",
        sa.Column("id_etiqueta", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id_etiqueta"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "libro_etiqueta",
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("id_etiqueta", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_etiqueta"], ["etiqueta.id_etiqueta"]),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"]),
        sa.PrimaryKeyConstraint("id_libro", "id_etiqueta"),
    )


def downgrade() -> None:
    op.drop_table("libro_etiqueta")
    op.drop_table("etiqueta")
