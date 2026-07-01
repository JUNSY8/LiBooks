"""Añade file_hash a libro para detección de duplicados.

Revision ID: 002
Revises: 001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("libro", schema=None) as batch_op:
        batch_op.add_column(sa.Column("file_hash", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_libro_file_hash", ["file_hash"])


def downgrade() -> None:
    with op.batch_alter_table("libro", schema=None) as batch_op:
        batch_op.drop_constraint("uq_libro_file_hash", type_="unique")
        batch_op.drop_column("file_hash")
