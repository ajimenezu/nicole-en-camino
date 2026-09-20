import pytest

from app.core import storage
from app.models.item import FotoItem


@pytest.fixture
def storage_configurado(monkeypatch):
    monkeypatch.setattr(storage, "esta_configurado", lambda: True)
    monkeypatch.setattr(
        storage, "presign_put", lambda key, ct: f"https://storage.fake/put/{key}"
    )
    monkeypatch.setattr(storage, "objeto_existe", lambda key: True)
    monkeypatch.setattr(storage, "borrar_objeto", lambda key: None)
    monkeypatch.setattr(storage, "url_publica", lambda key: f"https://cdn.fake/{key}")


def test_presign_sin_storage_503(client, auth_headers, item):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 503


def test_presign_ok(client, auth_headers, item, storage_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["key"].startswith(f"items/{item.id}/")
    assert body["upload_url"].startswith("https://storage.fake/put/")


def test_presign_tipo_no_permitido(client, auth_headers, item, storage_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "application/pdf", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_presign_muy_grande(client, auth_headers, item, storage_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 6 * 1024 * 1024},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_confirmar_foto_ok(client, auth_headers, item, storage_configurado):
    key = storage.generar_key(item.id, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["url"] == f"https://cdn.fake/{key}"


def test_confirmar_key_de_otro_item_422(
    client, auth_headers, item, storage_configurado
):
    key = storage.generar_key(item.id + 100, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_confirmar_objeto_inexistente_422(
    client, auth_headers, item, storage_configurado, monkeypatch
):
    monkeypatch.setattr(storage, "objeto_existe", lambda key: False)
    key = storage.generar_key(item.id, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_eliminar_foto(client, auth_headers, item, storage_configurado, db):
    foto = FotoItem(item_id=item.id, url="https://cdn.fake/items/1/x.jpg", orden=0)
    db.add(foto)
    db.commit()
    r = client.delete(f"/items/{item.id}/fotos/{foto.id}", headers=auth_headers)
    assert r.status_code == 204
    assert db.query(FotoItem).count() == 0


def test_eliminar_foto_inexistente_404(client, auth_headers, item):
    r = client.delete(f"/items/{item.id}/fotos/999", headers=auth_headers)
    assert r.status_code == 404


def test_fotos_requieren_auth(client, item):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 100},
    )
    assert r.status_code == 403


def test_key_pertenece_a_item():
    key_ok = "items/5/9c5b94b1-35ad-49bb-b118-8e8fc24abf80.jpg"
    assert storage.key_pertenece_a_item(key_ok, 5)
    assert not storage.key_pertenece_a_item(key_ok, 6)
    assert not storage.key_pertenece_a_item("otra/cosa.exe", 5)
    assert not storage.key_pertenece_a_item("items/5/../../evil.jpg", 5)


def test_key_desde_url(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "STORAGE_PUBLIC_URL", "https://cdn.fake")
    assert storage.key_desde_url("https://cdn.fake/items/1/a.jpg") == "items/1/a.jpg"
    assert storage.key_desde_url("https://otro.host/items/1/a.jpg") is None


def test_presign_apunta_al_bucket_con_path_style(monkeypatch):
    """Supabase solo acepta endpoint/bucket/key, y su endpoint ya trae un
    path propio: la URL tiene que conservarlo y firmar con su región."""
    from app.core.config import settings

    monkeypatch.setattr(
        settings,
        "STORAGE_ENDPOINT_URL",
        "https://abc.storage.supabase.co/storage/v1/s3",
    )
    monkeypatch.setattr(settings, "STORAGE_REGION", "us-east-1")
    monkeypatch.setattr(settings, "STORAGE_ACCESS_KEY_ID", "id-falso")
    monkeypatch.setattr(settings, "STORAGE_SECRET_ACCESS_KEY", "secreto-falso")
    monkeypatch.setattr(settings, "STORAGE_BUCKET", "fotos")

    assert storage.esta_configurado()
    url = storage.presign_put("items/1/a.jpg", "image/jpeg")
    assert url.startswith(
        "https://abc.storage.supabase.co/storage/v1/s3/fotos/items/1/a.jpg?"
    )
    assert "us-east-1" in url


def test_sin_endpoint_no_esta_configurado(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "STORAGE_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "STORAGE_ACCESS_KEY_ID", "id")
    monkeypatch.setattr(settings, "STORAGE_SECRET_ACCESS_KEY", "secreto")
    monkeypatch.setattr(settings, "STORAGE_BUCKET", "fotos")
    assert not storage.esta_configurado()
