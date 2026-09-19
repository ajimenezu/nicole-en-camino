"""nombre de la app: Nicole en Camino

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-09-19

La fila seed de wishlist_config nace con 'Julia en Camino' (ver
264cedb6c13a) y el nombre que se ve en la app sale de esa fila, no del
codigo. Cambiar el default en el modelo no alcanza para una base que ya
existe.

Solo se toca la fila si sigue con el nombre original: si alguien ya lo
cambio desde Ajustes, se respeta.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE wishlist_config SET nombre_app = 'Nicole en Camino' "
        "WHERE nombre_app = 'Julia en Camino'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE wishlist_config SET nombre_app = 'Julia en Camino' "
        "WHERE nombre_app = 'Nicole en Camino'"
    )
