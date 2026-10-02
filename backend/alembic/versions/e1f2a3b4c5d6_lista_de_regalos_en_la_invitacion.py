"""la invitación lleva a la lista de regalos

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-10-02

Interruptor por evento: si la invitación muestra el botón que lleva a la
wishlist. Nace prendido, también para las invitaciones que ya existen,
porque es el caso común —el baby shower— y apagarlo es un clic.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invitaciones",
        sa.Column(
            "muestra_wishlist",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("invitaciones", "muestra_wishlist")
