"""Clasificaciones jerarquicas para libros.

Revision ID: 006
Revises: 005
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clasificacion",
        sa.Column("id_clasificacion", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("id_padre", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id_padre"], ["clasificacion.id_clasificacion"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id_clasificacion"),
        sa.UniqueConstraint("nombre", "id_padre", name="uq_clasificacion_nombre_padre"),
    )
    op.create_table(
        "libro_clasificacion",
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("id_clasificacion", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_clasificacion"], ["clasificacion.id_clasificacion"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_libro", "id_clasificacion"),
    )


def downgrade() -> None:
    op.drop_table("libro_clasificacion")
    op.drop_table("clasificacion")
