from datetime import UTC, datetime, timedelta

from app.core import intentos_login
from app.routers import auth as auth_router


def test_login_ok(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_password_incorrecta(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "incorrecta"},
    )
    assert r.status_code == 401


def test_login_email_inexistente(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "nadie@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 401


def test_login_email_case_insensitive(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "ADMIN@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 200


def test_me_ok(client, admin, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


def test_me_token_invalido(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401


def test_me_sin_token(client):
    assert client.get("/auth/me").status_code == 403


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


class TestFrenoDeFuerzaBruta:
    """El freno cuenta por email y no por IP: sigue a la cuenta atacada
    aunque los intentos lleguen desde IPs distintas, y quien ataca solo se
    bloquea a si mismo."""

    def _fallar(self, client, veces, email="admin@test.com"):
        for _ in range(veces):
            client.post("/auth/login", json={"email": email, "password": "incorrecta"})

    def test_bloquea_tras_demasiados_fallos(self, client, admin):
        self._fallar(client, intentos_login.MAX_INTENTOS)
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "incorrecta"},
        )
        assert r.status_code == 429

    def test_bloquea_aunque_acierte_la_clave(self, client, admin):
        """Si no, bastaria con seguir probando hasta dar con la correcta."""
        self._fallar(client, intentos_login.MAX_INTENTOS)
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "clave-test-123"},
        )
        assert r.status_code == 429

    def test_un_login_correcto_borra_los_fallos(self, client, admin):
        self._fallar(client, intentos_login.MAX_INTENTOS - 1)
        ok = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "clave-test-123"},
        )
        assert ok.status_code == 200
        # El contador quedo en cero: vuelve a haber margen completo.
        self._fallar(client, intentos_login.MAX_INTENTOS - 1)
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "clave-test-123"},
        )
        assert r.status_code == 200

    def test_el_bloqueo_no_alcanza_a_otra_cuenta(self, client, admin):
        """Quien ataca se bloquea a si mismo, no al admin legitimo."""
        self._fallar(client, intentos_login.MAX_INTENTOS, email="otro@test.com")
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "clave-test-123"},
        )
        assert r.status_code == 200

    def test_los_fallos_viejos_no_cuentan(self, client, admin):
        """Fuera de la ventana el historial caduca solo."""
        viejo = datetime.now(UTC) - intentos_login.VENTANA - timedelta(seconds=1)
        intentos_login._fallos["admin@test.com"] = [viejo] * intentos_login.MAX_INTENTOS
        r = client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "clave-test-123"},
        )
        assert r.status_code == 200


def test_las_tres_rutas_de_docs_van_juntas():
    """El bug era justo este: docs y redoc apagados, pero el esquema
    seguia publico en /openapi.json, que es de donde salen los dos. O se
    exponen las tres, o ninguna."""
    from main import app

    rutas = [app.docs_url, app.redoc_url, app.openapi_url]
    assert all(r is None for r in rutas) or all(r is not None for r in rutas)


def test_el_email_inexistente_cuesta_lo_mismo(client, admin, monkeypatch):
    """Sin esto, el tiempo de respuesta delata si un email esta registrado:
    bcrypt solo correria en el caso "la cuenta existe".

    Se comprueba que la verificacion ocurre, no cuanto tarda: un test de
    tiempos seria inestable en CI.
    """
    llamadas = []
    original = auth_router.verify_password

    def espia(plain, hashed):
        llamadas.append(hashed)
        return original(plain, hashed)

    monkeypatch.setattr(auth_router, "verify_password", espia)

    client.post(
        "/auth/login",
        json={"email": "nadie@test.com", "password": "loquesea"},
    )

    assert llamadas, "no se verifico nada para un email inexistente"
    assert llamadas[0] == auth_router._HASH_DE_DESCARTE
