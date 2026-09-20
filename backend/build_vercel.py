"""Paso de build en Vercel: migraciones y cuenta admin.

Vercel lo corre en cada deploy, después de instalar las dependencias (ver
`[tool.vercel.scripts]` en pyproject.toml). Cumple el papel que tenía el
preDeployCommand de Railway.

Solo actúa en producción. Los deploys de preview comparten las variables
del proyecto, así que uno de una rama sin mergear migraría la base real
con código que nadie aprobó. vercel.json ya saltea esos builds; esta
guarda es la segunda línea por si alguien cambia esa configuración.
"""

import os
import sys

from alembic.config import Config

from alembic import command


def main() -> int:
    if os.environ.get("VERCEL_ENV") != "production":
        print("No es un deploy de producción: no se migra ni se toca el admin.")
        return 0

    command.upgrade(Config("alembic.ini"), "head")

    # Después de migrar, porque necesita la tabla admins. Sin
    # ADMIN_EMAIL/ADMIN_PASSWORD no hace nada.
    import seed_admin

    return seed_admin.main()


if __name__ == "__main__":
    sys.exit(main())
