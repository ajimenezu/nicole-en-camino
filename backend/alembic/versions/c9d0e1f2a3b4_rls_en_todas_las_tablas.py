"""rls en todas las tablas

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-19

Supabase publica automaticamente cada tabla del schema public en su API
REST, y la llave con que se accede a esa API (la anon key) no es secreta:
cualquier app del proyecto la manda al navegador. Sin RLS, con esa llave
se podria leer reservas (el nombre de quien regala, que es justo la
sorpresa), admins (los hashes de las contrasenas) y todo lo demas.

La app no usa esa API: el backend se conecta directo a Postgres como
dueno de las tablas, y el dueno no pasa por RLS. Asi que activar RLS sin
ninguna policy cierra la API REST por completo sin tocar a la app.

Una tabla nueva que se agregue despues necesita lo mismo en su propia
migracion. En Postgres local no cambia nada, por la misma razon: el
usuario de la app es el dueno.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = [
    "admins",
    "alembic_version",
    "cajas_almacenamiento",
    "categorias",
    "fotos_item",
    "fotos_regalo",
    "invitaciones",
    "items",
    "regalos",
    "reservas",
    "rsvps",
    "wishlist_config",
]


def upgrade() -> None:
    for tabla in TABLAS:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for tabla in TABLAS:
        op.execute(f"ALTER TABLE {tabla} DISABLE ROW LEVEL SECURITY")
