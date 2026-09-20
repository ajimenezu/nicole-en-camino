"""fecha probable de parto

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-19

La fecha de la cuenta regresiva. Va en wishlist_config y no en una tabla
nueva porque es un dato único de la app, igual que el nombre.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("wishlist_config", sa.Column("fecha_parto", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("wishlist_config", "fecha_parto")
