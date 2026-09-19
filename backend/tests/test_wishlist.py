from app.core.ratelimit import limiter
from app.models.item import EstadoItem

TOKEN = "11111111-1111-1111-1111-111111111111"


def test_wishlist_publica_solo_necesitados(client, config, item, db):
    from app.models.item import Item

    adquirido = Item(nombre="Ya comprado", estado=EstadoItem.ADQUIRIDO)
    db.add(adquirido)
    db.commit()
    w = client.get(f"/w/{TOKEN}")
    assert w.status_code == 200
    ids = [x["id"] for x in w.json()["items"]]
    assert item.id in ids
    assert adquirido.id not in ids


def test_wishlist_publica_incluye_nombre_app(client, config, item):
    assert client.get(f"/w/{TOKEN}").json()["nombre_app"] == "Nicole en Camino"


def test_wishlist_publica_no_expone_campos_privados(client, config, item):
    data = client.get(f"/w/{TOKEN}").json()["items"][0]
    assert "estado" not in data
    assert "gifter_name" not in data
    assert "origen_adquisicion" not in data


def test_wishlist_token_invalido_404(client, config):
    assert client.get("/w/token-falso").status_code == 404


def test_config_default(client, config):
    r = client.get("/config")
    assert r.status_code == 200
    # Solo el nombre: los datos del evento se sirven contra el token de
    # la invitación, para que el lugar y la hora no queden consultables
    # sin tener el link.
    assert r.json() == {"nombre_app": "Nicole en Camino"}


def test_config_update_admin(client, auth_headers, config):
    r = client.patch(
        "/config", json={"nombre_app": "Esperando a Nicole"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert client.get("/config").json()["nombre_app"] == "Esperando a Nicole"


def test_config_update_requiere_auth(client, config):
    assert client.patch("/config", json={"nombre_app": "Hack"}).status_code == 403


def test_config_update_vacio_422(client, auth_headers, config):
    r = client.patch("/config", json={"nombre_app": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_link_wishlist_admin(client, auth_headers, config):
    r = client.get("/wishlist/link", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["share_token"] == TOKEN


def test_link_requiere_auth(client, config):
    assert client.get("/wishlist/link").status_code == 403


def test_rate_limit_en_endpoints_publicos(client, config):
    limiter.enabled = True
    limiter.reset()
    try:
        codes = [client.get("/config").status_code for _ in range(35)]
        assert codes[:30] == [200] * 30
        assert 429 in codes[30:]
    finally:
        limiter.reset()
        limiter.enabled = False
