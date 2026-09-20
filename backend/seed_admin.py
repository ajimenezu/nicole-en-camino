"""Crea (o actualiza) la cuenta admin única desde variables de entorno.

Uso local:
    ADMIN_EMAIL=pareja@example.com ADMIN_PASSWORD=... python seed_admin.py

En Vercel corre solo, en el build de producción (ver build_vercel.py): si
las variables no están definidas no hace nada y termina bien, así puede
quedar siempre en el pipeline sin romper los deploys. Conviene definirlas
para el primer deploy y borrarlas después: mientras estén, cada deploy
vuelve a poner esa contraseña.

Es idempotente: si el email ya existe, actualiza la contraseña.
"""

import os
import sys

from email_validator import EmailNotValidError, validate_email

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import Admin


def main() -> int:
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")

    if not email and not password:
        # Sin variables no hay nada que hacer. No es un error: permite
        # dejar este script en el pre-deploy de forma permanente.
        print("ADMIN_EMAIL/ADMIN_PASSWORD no definidos: no se crea ninguna cuenta.")
        return 0

    if not email or not password:
        print("ERROR: hay que definir ADMIN_EMAIL y ADMIN_PASSWORD, no solo una.")
        return 1
    if len(password) < 8:
        print("ERROR: ADMIN_PASSWORD debe tener al menos 8 caracteres.")
        return 1
    # La misma validación que aplica el login (EmailStr): sin esto se podía
    # crear una cuenta con un email que después el login rechaza, por
    # ejemplo uno de dominio .local, y quedaba imposible entrar.
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        print(f"ERROR: ADMIN_EMAIL no es un email válido para el login: {e}")
        return 1

    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if admin:
            admin.password_hash = hash_password(password)
            accion = "actualizada"
        else:
            admin = Admin(email=email, password_hash=hash_password(password))
            db.add(admin)
            accion = "creada"
        db.commit()
        print(f"Cuenta admin {accion}: {email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
