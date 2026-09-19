import pytest

from app.core import storage_r2
from app.models.regalo import FotoRegalo, Regalo


@pytest.fixture
def regalo(db, item) -> Regalo:
    r = Regalo(item_id=item.id, persona="Prima Sofía", cantidad=1)
    db.add(r)
    db.commit()
    return r


@pytest.fixture
def r2_configurado(monkeypatch):
    monkeypatch.setattr(storage_r2, "esta_configurado", lambda: True)
    monkeypatch.setattr(
        storage_r2, "presign_put", lambda key, ct: f"https://r2.fake/put/{key}"
    )
    monkeypatch.setattr(storage_r2, "objeto_existe", lambda key: True)
    monkeypatch.setattr(storage_r2, "borrar_objeto", lambda key: None)
    monkeypatch.setattr(
        storage_r2, "url_publica", lambda key: f"https://cdn.fake/{key}"
    )


def test_presign_sin_r2_da_503(client, auth_headers, regalo):
    r = client.post(
        f"/regalos/{regalo.id}/fotos/presign",
        json={"content_type": "image/jpeg", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 503


def test_presign_usa_el_prefijo_de_regalos(
    client, auth_headers, regalo, r2_configurado
):
    r = client.post(
        f"/regalos/{regalo.id}/fotos/presign",
        json={"content_type": "image/jpeg", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    # El prefijo separa las fotos de Nicole de las de referencia del catálogo.
    assert r.json()["key"].startswith(f"regalos/{regalo.id}/")


def test_presign_tipo_no_permitido(client, auth_headers, regalo, r2_configurado):
    r = client.post(
        f"/regalos/{regalo.id}/fotos/presign",
        json={"content_type": "video/mp4", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_presign_muy_grande(client, auth_headers, regalo, r2_configurado):
    r = client.post(
        f"/regalos/{regalo.id}/fotos/presign",
        json={"content_type": "image/jpeg", "size_bytes": 6 * 1024 * 1024},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_confirmar_foto(client, auth_headers, regalo, r2_configurado):
    key = storage_r2.generar_key(regalo.id, "image/jpeg", prefijo="regalos")
    r = client.post(
        f"/regalos/{regalo.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["url"] == f"https://cdn.fake/{key}"


def test_key_de_otro_regalo_da_422(client, auth_headers, regalo, r2_configurado):
    key = storage_r2.generar_key(regalo.id + 100, "image/jpeg", prefijo="regalos")
    r = client.post(
        f"/regalos/{regalo.id}/fotos", json={"key": key}, headers=auth_headers
    )
    assert r.status_code == 422


def test_key_de_item_no_sirve_para_regalo(client, auth_headers, regalo, r2_configurado):
    """Una key del catálogo no puede colarse como foto de un regalo."""
    key = storage_r2.generar_key(regalo.id, "image/jpeg", prefijo="items")
    r = client.post(
        f"/regalos/{regalo.id}/fotos", json={"key": key}, headers=auth_headers
    )
    assert r.status_code == 422


def test_la_foto_aparece_en_el_regalo(client, auth_headers, regalo, r2_configurado):
    key = storage_r2.generar_key(regalo.id, "image/jpeg", prefijo="regalos")
    client.post(f"/regalos/{regalo.id}/fotos", json={"key": key}, headers=auth_headers)
    listado = client.get("/regalos", headers=auth_headers).json()
    assert len(listado[0]["fotos"]) == 1


def test_eliminar_foto(client, auth_headers, regalo, r2_configurado, db):
    foto = FotoRegalo(
        regalo_id=regalo.id, url="https://cdn.fake/regalos/1/a.jpg", orden=0
    )
    db.add(foto)
    db.commit()
    r = client.delete(f"/regalos/{regalo.id}/fotos/{foto.id}", headers=auth_headers)
    assert r.status_code == 204
    assert db.query(FotoRegalo).count() == 0


def test_eliminar_foto_inexistente_da_404(client, auth_headers, regalo):
    r = client.delete(f"/regalos/{regalo.id}/fotos/999", headers=auth_headers)
    assert r.status_code == 404


def test_borrar_el_regalo_borra_sus_fotos(
    client, auth_headers, regalo, r2_configurado, db
):
    db.add(FotoRegalo(regalo_id=regalo.id, url="https://cdn.fake/regalos/1/a.jpg"))
    db.commit()
    client.delete(f"/regalos/{regalo.id}", headers=auth_headers)
    assert db.query(FotoRegalo).count() == 0


def test_fotos_requieren_auth(client, regalo):
    r = client.post(
        f"/regalos/{regalo.id}/fotos/presign",
        json={"content_type": "image/jpeg", "size_bytes": 100},
    )
    assert r.status_code == 403


def test_key_pertenece_valida_el_prefijo():
    uuid_falso = "9c5b94b1-35ad-49bb-b118-8e8fc24abf80"
    assert storage_r2.key_pertenece_a_item(
        f"regalos/5/{uuid_falso}.jpg", 5, prefijo="regalos"
    )
    assert not storage_r2.key_pertenece_a_item(
        f"items/5/{uuid_falso}.jpg", 5, prefijo="regalos"
    )
    assert not storage_r2.key_pertenece_a_item(
        f"regalos/5/{uuid_falso}.jpg", 5, prefijo="items"
    )
    assert not storage_r2.key_pertenece_a_item("regalos/5/../evil.jpg", 5, "regalos")
