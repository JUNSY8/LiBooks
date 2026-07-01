"""Anotaciones PDF: notas ancladas y resaltados.

Revision ID: 003
Revises: 002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("nota", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pagina", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("fragmento", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("rects", sa.Text(), nullable=True))

    op.create_table(
        "resaltado",
        sa.Column("id_resaltado", sa.Integer(), nullable=False),
        sa.Column("id_libro", sa.Integer(), nullable=False),
        sa.Column("pagina", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=True),
        sa.Column("rects", sa.Text(), nullable=False),
        sa.Column("fecha_creacion", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(["id_libro"], ["libro.id_libro"]),
        sa.PrimaryKeyConstraint("id_resaltado"),
    )


def downgrade() -> None:
    op.drop_table("resaltado")
    with op.batch_alter_table("nota", schema=None) as batch_op:
        batch_op.drop_column("rects")
        batch_op.drop_column("fragmento")
        batch_op.drop_column("pagina")
