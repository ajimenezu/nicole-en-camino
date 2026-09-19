"""El muro de agradecimiento de la página pública."""

TOKEN = "11111111-1111-1111-1111-111111111111"


def test_muro_lista_los_regalos_recibidos(client, auth_headers, config, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Familia López"},
        headers=auth_headers,
    )
    muro = client.get(f"/w/{TOKEN}").json()["recibidos"]
    assert len(muro) == 1
    assert muro[0]["item"] == item.nombre
    assert muro[0]["persona"] == "Familia López"


def test_muro_excluye_las_compras_propias(client, auth_headers, config, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "origen": "NOSOTROS"},
        headers=auth_headers,
    )
    assert client.get(f"/w/{TOKEN}").json()["recibidos"] == []


def test_una_reserva_pendiente_no_llega_al_muro(client, config, item):
    """La sorpresa: mientras está reservado no hay regalo, así que el
    nombre no puede aparecer en público."""
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Tía Secreta"})
    publico = client.get(f"/w/{TOKEN}")
    assert publico.json()["recibidos"] == []
    assert "Tía Secreta" not in publico.text


def test_el_nombre_aparece_recien_al_recibir(client, auth_headers, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Tía Secreta"})
    reservas = client.get(f"/items/{item.id}/reservas", headers=auth_headers).json()
    client.post(
        f"/items/{item.id}/reservas/{reservas[0]['id']}/recibir",
        headers=auth_headers,
    )
    muro = client.get(f"/w/{TOKEN}").json()["recibidos"]
    assert [r["persona"] for r in muro] == ["Tía Secreta"]


def test_el_muro_no_expone_la_nota_privada(client, auth_headers, config, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Ana", "nota": "secreto entre nosotros"},
        headers=auth_headers,
    )
    publico = client.get(f"/w/{TOKEN}")
    assert "secreto entre nosotros" not in publico.text


def test_el_muro_usa_la_foto_de_nicole_si_existe(
    client, auth_headers, config, item, db
):
    from app.models.item import FotoItem
    from app.models.regalo import FotoRegalo

    db.add(FotoItem(item_id=item.id, url="https://cdn.test/items/ref.jpg"))
    db.commit()
    r = client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Ana"},
        headers=auth_headers,
    ).json()

    # Sin foto de Nicole todavía, cae a la de referencia del catálogo.
    assert client.get(f"/w/{TOKEN}").json()["recibidos"][0]["foto"].endswith("ref.jpg")

    db.add(FotoRegalo(regalo_id=r["id"], url="https://cdn.test/regalos/nicole.jpg"))
    db.commit()
    assert (
        client.get(f"/w/{TOKEN}").json()["recibidos"][0]["foto"].endswith("nicole.jpg")
    )


def test_el_muro_no_necesita_auth(client, auth_headers, config, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Ana"},
        headers=auth_headers,
    )
    assert client.get(f"/w/{TOKEN}").status_code == 200


def test_muro_vacio_al_principio(client, config, item):
    assert client.get(f"/w/{TOKEN}").json()["recibidos"] == []
