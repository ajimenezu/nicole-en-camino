"""Confirmacion de asistencia al baby shower."""

from app.models.invitacion import Invitacion
from app.models.rsvp import Rsvp
from app.models.wishlist_config import WishlistConfig


def _config(db) -> WishlistConfig:
    config = db.query(WishlistConfig).first()
    if not config:
        config = WishlistConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _invitacion(db, titulo: str = "Baby shower") -> Invitacion:
    inv = db.query(Invitacion).filter(Invitacion.titulo == titulo).first()
    if not inv:
        inv = Invitacion(titulo=titulo)
        db.add(inv)
        db.commit()
        db.refresh(inv)
    return inv


def _token(db) -> str:
    """El token de la invitacion, que es con el que se confirma."""
    return _invitacion(db).token


class TestResponder:
    def test_alguien_con_el_link_puede_confirmar(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp",
            json={"nombre": "Hannia Solano", "asistira": True},
        )
        assert r.status_code == 201
        assert r.json()["nombre"] == "Hannia Solano"
        assert r.json()["asistira"] is True

    def test_tambien_se_puede_decir_que_no(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp", json={"nombre": "Ana", "asistira": False}
        )
        assert r.status_code == 201
        assert r.json()["asistira"] is False

    def test_un_token_inventado_no_sirve(self, client):
        r = client.post(
            "/i/token-que-no-existe/rsvp",
            json={"nombre": "Colado", "asistira": True},
        )
        assert r.status_code == 404

    def test_el_nombre_no_puede_ser_espacios(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp", json={"nombre": "   ", "asistira": True}
        )
        assert r.status_code == 422

    def test_el_nombre_se_guarda_sin_espacios_de_sobra(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp",
            json={"nombre": "  Marta  ", "asistira": True},
        )
        assert r.json()["nombre"] == "Marta"


class TestConsultaDelAdmin:
    def test_lista_con_los_totales(self, client, auth_headers, db):
        db.add(Rsvp(invitacion_id=_invitacion(db).id, nombre="Ana", asistira=True))
        db.add(Rsvp(invitacion_id=_invitacion(db).id, nombre="Beto", asistira=True))
        db.add(Rsvp(invitacion_id=_invitacion(db).id, nombre="Caro", asistira=False))
        db.commit()

        r = client.get("/rsvps", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["asisten"] == 2
        assert r.json()["no_asisten"] == 1
        assert len(r.json()["respuestas"]) == 3

    def test_sin_sesion_no_se_puede_ver_quien_viene(self, client, db):
        db.add(Rsvp(invitacion_id=_invitacion(db).id, nombre="Ana", asistira=True))
        db.commit()

        r = client.get("/rsvps")
        assert r.status_code in (401, 403)

    def test_se_puede_borrar_una_respuesta_cargada_por_error(
        self, client, auth_headers, db
    ):
        rsvp = Rsvp(invitacion_id=_invitacion(db).id, nombre="Duplicada", asistira=True)
        db.add(rsvp)
        db.commit()

        r = client.delete(f"/rsvps/{rsvp.id}", headers=auth_headers)
        assert r.status_code == 204
        assert db.query(Rsvp).filter(Rsvp.id == rsvp.id).first() is None

    def test_borrar_algo_que_no_existe_da_404(self, client, auth_headers):
        assert client.delete("/rsvps/9999", headers=auth_headers).status_code == 404


class TestDatosDelEvento:
    def test_la_invitacion_devuelve_sus_datos(self, client, auth_headers, db):
        inv = _invitacion(db)
        client.patch(
            f"/invitaciones/{inv.id}",
            json={"lugar": "Salón El Jardín", "fecha": "Sábado 15"},
            headers=auth_headers,
        )
        datos = client.get(f"/i/{inv.token}").json()
        assert datos["lugar"] == "Salón El Jardín"
        assert datos["fecha"] == "Sábado 15"

    def test_se_puede_cambiar_solo_uno_sin_pisar_los_demas(
        self, client, auth_headers, db
    ):
        inv = _invitacion(db)
        client.patch(
            f"/invitaciones/{inv.id}",
            json={"lugar": "Casa", "hora": "5 pm"},
            headers=auth_headers,
        )
        client.patch(
            f"/invitaciones/{inv.id}", json={"hora": "6 pm"}, headers=auth_headers
        )
        datos = client.get(f"/i/{inv.token}").json()
        assert datos["lugar"] == "Casa"
        assert datos["hora"] == "6 pm"

    def test_vaciar_un_campo_lo_borra(self, client, auth_headers, db):
        inv = _invitacion(db)
        client.patch(
            f"/invitaciones/{inv.id}", json={"hora": "5 pm"}, headers=auth_headers
        )
        client.patch(f"/invitaciones/{inv.id}", json={"hora": ""}, headers=auth_headers)
        assert client.get(f"/i/{inv.token}").json()["hora"] is None

    def test_el_titulo_no_se_muestra_a_quien_recibe_el_link(self, client, db):
        inv = _invitacion(db, "Interno: tanda de la familia")
        assert "titulo" not in client.get(f"/i/{inv.token}").json()


class TestLinksSeparados:
    def test_el_token_de_la_wishlist_no_sirve_para_confirmar(self, client, db):
        config = _config(db)
        r = client.post(
            f"/i/{config.share_token}/rsvp",
            json={"nombre": "Colado", "asistira": True},
        )
        assert r.status_code == 404

    def test_el_token_de_la_invitacion_no_abre_la_wishlist(self, client, db):
        assert client.get(f"/w/{_token(db)}").status_code == 404

    def test_un_token_de_invitacion_inventado_da_404(self, client):
        assert client.get("/i/no-existe").status_code == 404


class TestVariasInvitaciones:
    def test_cada_una_tiene_su_propio_link(self, client, auth_headers):
        a = client.post(
            "/invitaciones", json={"titulo": "Tanda familia"}, headers=auth_headers
        ).json()
        b = client.post(
            "/invitaciones", json={"titulo": "Tanda amigas"}, headers=auth_headers
        ).json()
        assert a["token"] != b["token"]

    def test_las_confirmaciones_no_se_mezclan(self, client, auth_headers, db):
        a = client.post(
            "/invitaciones", json={"titulo": "Familia"}, headers=auth_headers
        ).json()
        b = client.post(
            "/invitaciones", json={"titulo": "Amigas"}, headers=auth_headers
        ).json()

        client.post(
            f"/i/{a['token']}/rsvp", json={"nombre": "Tia Ana", "asistira": True}
        )
        client.post(f"/i/{b['token']}/rsvp", json={"nombre": "Sofia", "asistira": True})
        client.post(
            f"/i/{b['token']}/rsvp", json={"nombre": "Marta", "asistira": False}
        )

        por_id = {
            i["id"]: i for i in client.get("/invitaciones", headers=auth_headers).json()
        }
        assert por_id[a["id"]]["asisten"] == 1
        assert por_id[b["id"]]["asisten"] == 1
        assert por_id[b["id"]]["no_asisten"] == 1

    def test_borrar_una_se_lleva_sus_confirmaciones(self, client, auth_headers, db):
        inv = client.post(
            "/invitaciones", json={"titulo": "Se borra"}, headers=auth_headers
        ).json()
        client.post(
            f"/i/{inv['token']}/rsvp", json={"nombre": "Alguien", "asistira": True}
        )

        assert (
            client.delete(
                f"/invitaciones/{inv['id']}", headers=auth_headers
            ).status_code
            == 204
        )
        assert db.query(Rsvp).filter(Rsvp.invitacion_id == inv["id"]).count() == 0

    def test_sin_sesion_no_se_pueden_listar(self, client):
        assert client.get("/invitaciones").status_code in (401, 403)

    def test_el_titulo_es_obligatorio(self, client, auth_headers):
        r = client.post("/invitaciones", json={"titulo": "  "}, headers=auth_headers)
        assert r.status_code == 422


class TestComentarioParaNicole:
    def test_se_guarda_el_comentario(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp",
            json={
                "nombre": "Hannia",
                "asistira": True,
                "comentario": "Te esperamos con muchas ganas, Nicole",
            },
        )
        assert r.status_code == 201
        assert r.json()["comentario"] == "Te esperamos con muchas ganas, Nicole"

    def test_es_opcional(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp", json={"nombre": "Sin mensaje", "asistira": True}
        )
        assert r.status_code == 201
        assert r.json()["comentario"] is None

    def test_un_comentario_en_blanco_no_se_guarda(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp",
            json={"nombre": "Ana", "asistira": True, "comentario": "   "},
        )
        assert r.json()["comentario"] is None


class TestCambiarLaPropiaRespuesta:
    def _crear(self, client, db, **extra):
        cuerpo = {"nombre": "Ana", "asistira": True, **extra}
        return client.post(f"/i/{_token(db)}/rsvp", json=cuerpo).json()

    def test_al_confirmar_devuelve_el_token_para_editar(self, client, db):
        assert self._crear(client, db)["token_edicion"]

    def test_cambiar_no_crea_otra_respuesta(self, client, db):
        creada = self._crear(client, db)
        antes = db.query(Rsvp).count()

        r = client.patch(
            f"/i/{_token(db)}/rsvp/{creada['token_edicion']}",
            json={"asistira": False},
        )
        assert r.status_code == 200
        assert r.json()["asistira"] is False
        assert db.query(Rsvp).count() == antes

    def test_se_puede_cambiar_el_nombre_y_el_comentario(self, client, db):
        creada = self._crear(client, db, comentario="Original")
        r = client.patch(
            f"/i/{_token(db)}/rsvp/{creada['token_edicion']}",
            json={"nombre": "Ana Perez", "comentario": "Corregido"},
        )
        assert r.json()["nombre"] == "Ana Perez"
        assert r.json()["comentario"] == "Corregido"

    def test_con_un_token_ajeno_no_se_puede(self, client, db):
        self._crear(client, db)
        r = client.patch(
            f"/i/{_token(db)}/rsvp/token-inventado", json={"asistira": False}
        )
        assert r.status_code == 404

    def test_el_token_no_sirve_en_otra_invitacion(self, client, auth_headers, db):
        creada = self._crear(client, db)
        otra = client.post(
            "/invitaciones", json={"titulo": "Otra"}, headers=auth_headers
        ).json()

        r = client.patch(
            f"/i/{otra['token']}/rsvp/{creada['token_edicion']}",
            json={"asistira": False},
        )
        assert r.status_code == 404

    def test_el_admin_no_ve_el_token_en_el_listado(self, client, auth_headers, db):
        self._crear(client, db)
        listado = client.get("/rsvps", headers=auth_headers).json()
        assert "token_edicion" not in listado["respuestas"][0]

    def test_no_se_puede_dejar_el_nombre_vacio(self, client, db):
        creada = self._crear(client, db)
        r = client.patch(
            f"/i/{_token(db)}/rsvp/{creada['token_edicion']}", json={"nombre": "  "}
        )
        assert r.status_code == 422


class TestCuantosVienen:
    def test_por_defecto_no_se_pregunta(self, client, auth_headers):
        inv = client.post(
            "/invitaciones", json={"titulo": "Amigas"}, headers=auth_headers
        ).json()
        assert inv["pide_cantidad"] is False
        assert client.get(f"/i/{inv['token']}").json()["pide_cantidad"] is False

    def test_se_puede_activar_por_invitacion(self, client, auth_headers):
        inv = client.post(
            "/invitaciones", json={"titulo": "Familias"}, headers=auth_headers
        ).json()
        client.patch(
            f"/invitaciones/{inv['id']}",
            json={"pide_cantidad": True},
            headers=auth_headers,
        )
        assert client.get(f"/i/{inv['token']}").json()["pide_cantidad"] is True

    def test_se_puede_volver_a_desactivar(self, client, auth_headers):
        inv = client.post(
            "/invitaciones",
            json={"titulo": "Cambia", "pide_cantidad": True},
            headers=auth_headers,
        ).json()
        client.patch(
            f"/invitaciones/{inv['id']}",
            json={"pide_cantidad": False},
            headers=auth_headers,
        )
        assert client.get(f"/i/{inv['token']}").json()["pide_cantidad"] is False

    def test_se_guarda_como_texto_libre(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp",
            json={
                "nombre": "Familia Solano",
                "asistira": True,
                "cantidad": "2 adultos y 1 bebé",
            },
        )
        assert r.status_code == 201
        assert r.json()["cantidad"] == "2 adultos y 1 bebé"

    def test_es_opcional(self, client, db):
        r = client.post(
            f"/i/{_token(db)}/rsvp", json={"nombre": "Sola", "asistira": True}
        )
        assert r.json()["cantidad"] is None

    def test_se_puede_corregir_al_cambiar_la_respuesta(self, client, db):
        creada = client.post(
            f"/i/{_token(db)}/rsvp",
            json={"nombre": "Ana", "asistira": True, "cantidad": "2"},
        ).json()
        r = client.patch(
            f"/i/{_token(db)}/rsvp/{creada['token_edicion']}",
            json={"cantidad": "3, se suma mi hermana"},
        )
        assert r.json()["cantidad"] == "3, se suma mi hermana"
