"""El seed corre en cada deploy de producción, así que su comportamiento
sin variables definidas importa: no debe romper el pipeline."""

import seed_admin
from app.models.admin import Admin


def test_sin_variables_no_hace_nada_y_sale_bien(monkeypatch, capsys):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert seed_admin.main() == 0
    assert "no se crea" in capsys.readouterr().out


def test_solo_una_variable_es_error(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "a@b.com")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert seed_admin.main() == 1


def test_password_corta_es_error(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "a@b.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "corta")
    assert seed_admin.main() == 1


def test_crea_la_cuenta(monkeypatch, db):
    monkeypatch.setattr(seed_admin, "SessionLocal", lambda: db)
    monkeypatch.setenv("ADMIN_EMAIL", "Nuevo@Ejemplo.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "clave-larga-123")

    assert seed_admin.main() == 0
    creado = db.query(Admin).filter(Admin.email == "nuevo@ejemplo.com").one()
    assert creado.password_hash != "clave-larga-123"


def test_es_idempotente(monkeypatch, db, admin):
    """Correrlo de nuevo actualiza la contraseña en vez de fallar: es lo
    que permite dejarlo en el pre-deploy."""
    monkeypatch.setattr(seed_admin, "SessionLocal", lambda: db)
    email = admin.email
    hash_viejo = admin.password_hash
    monkeypatch.setenv("ADMIN_EMAIL", email)
    monkeypatch.setenv("ADMIN_PASSWORD", "otra-clave-larga")

    assert seed_admin.main() == 0

    # El script cierra la sesión, así que se vuelve a consultar en vez de
    # refrescar la instancia (que quedó desasociada).
    assert db.query(Admin).count() == 1
    actualizado = db.query(Admin).filter(Admin.email == email).one()
    assert actualizado.password_hash != hash_viejo


def test_email_que_el_login_rechaza_es_error(monkeypatch, capsys):
    """Un dominio .local pasa como texto pero el login lo rechaza: crear
    esa cuenta dejaría al admin sin forma de entrar."""
    monkeypatch.setenv("ADMIN_EMAIL", "admin@casa.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "clave-larga-123")
    assert seed_admin.main() == 1
    assert "no es un email válido" in capsys.readouterr().out
