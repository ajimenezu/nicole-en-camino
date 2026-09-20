"""La clave de los límites de tasa: una por persona, no una para todos."""

from starlette.requests import Request

from app.core.ratelimit import ip_del_cliente


def _pedido(headers: dict[str, str], ip_socket: str = "10.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
            "client": (ip_socket, 1234),
        }
    )


def test_en_vercel_usa_la_ip_real_del_header(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert ip_del_cliente(_pedido({"x-real-ip": "203.0.113.7"})) == "203.0.113.7"


def test_en_vercel_dos_invitados_no_comparten_balde(monkeypatch):
    """El caso que motivó el cambio: detrás del proxy la IP del socket es
    la misma para todos, pero cada invitado tiene que contar aparte."""
    monkeypatch.setenv("VERCEL", "1")
    ana = ip_del_cliente(_pedido({"x-real-ip": "203.0.113.7"}, ip_socket="10.0.0.1"))
    beto = ip_del_cliente(_pedido({"x-real-ip": "198.51.100.4"}, ip_socket="10.0.0.1"))
    assert ana != beto


def test_en_vercel_sin_header_cae_a_la_conexion(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert ip_del_cliente(_pedido({})) == "10.0.0.1"


def test_fuera_de_vercel_no_le_cree_al_header(monkeypatch):
    """Sin el proxy de Vercel delante, el header lo escribe el cliente:
    creerle permitiría saltarse el límite cambiándolo en cada pedido."""
    monkeypatch.delenv("VERCEL", raising=False)
    assert ip_del_cliente(_pedido({"x-real-ip": "203.0.113.7"})) == "10.0.0.1"
