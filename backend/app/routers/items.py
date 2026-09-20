from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core import storage
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.categoria import Categoria
from app.models.item import EstadoItem, Etapa, Item
from app.models.regalo import OrigenRegalo, Regalo
from app.models.reserva import Reserva
from app.schemas.item import (
    ItemAdquirir,
    ItemBusquedaOut,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    ReservaAdminOut,
    ReservaReveladaOut,
)
from app.services.items import (
    contar_reservas_activas,
    recalcular_item,
    reservas_activas,
)

router = APIRouter(prefix="/items", tags=["items"])

_ACENTOS_DESDE = "áéíóúüñÁÉÍÓÚÜÑ"
_ACENTOS_HASTA = "aeiounnAEIOUNN"


def _cargado(query):
    return query.options(
        selectinload(Item.fotos),
        selectinload(Item.caja),
        selectinload(Item.categoria),
        selectinload(Item.reservas),
        selectinload(Item.regalos),
    )


def _get_item_or_404(item_id: int, db: Session) -> Item:
    item = _cargado(db.query(Item)).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


def _validar_categoria(db: Session, categoria_id: int | None) -> None:
    if categoria_id is None:
        return
    if not db.query(Categoria).filter(Categoria.id == categoria_id).first():
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def crear_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _validar_categoria(db, body.categoria_id)
    item = Item(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ItemOut])
def listar_items(
    etapa: Etapa | None = None,
    estado: EstadoItem | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = _cargado(db.query(Item))
    if etapa is not None:
        query = query.filter(Item.etapa == etapa)
    if estado is not None:
        query = query.filter(Item.estado == estado)
    return query.order_by(Item.created_at.desc()).all()


@router.get("/buscar", response_model=list[ItemBusquedaOut])
def buscar_items(
    q: str | None = Query(default=None, max_length=100),
    persona: str | None = Query(default=None, max_length=255),
    etapa: Etapa | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Busca por nombre y descripción, o por quién lo regaló.

    Devuelve lo necesario para responder de una: dónde está guardado, para
    qué etapa sirve y quién lo regaló.

    `persona` trae los objetos que regaló alguien, con coincidencia
    parcial: es la búsqueda "¿qué me regaló fulano?", que de otro modo
    obliga a recorrer la lista entera a ojo.
    """
    if not (q or "").strip() and not (persona or "").strip():
        raise HTTPException(
            status_code=422, detail="Indicá un texto a buscar o una persona"
        )

    def sin_acentos(col):
        return func.translate(func.lower(col), _ACENTOS_DESDE, _ACENTOS_HASTA)

    def patron_de(texto: str) -> str:
        normalizado = texto.strip().translate(
            str.maketrans(_ACENTOS_DESDE, _ACENTOS_HASTA)
        )
        return f"%{normalizado.lower()}%"

    query = db.query(Item).options(
        selectinload(Item.caja),
        selectinload(Item.regalos),
        selectinload(Item.fotos),
    )

    if (q or "").strip():
        patron = patron_de(q)
        query = query.filter(
            sin_acentos(Item.nombre).like(patron)
            | sin_acentos(func.coalesce(Item.descripcion, "")).like(patron)
        )

    if (persona or "").strip():
        query = query.filter(
            Item.regalos.any(sin_acentos(Regalo.persona).like(patron_de(persona)))
        )
    if etapa is not None:
        query = query.filter(Item.etapa == etapa)
    return query.order_by(Item.nombre).limit(50).all()


@router.patch("/{item_id}", response_model=ItemOut)
def editar_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = _get_item_or_404(item_id, db)
    cambios = body.model_dump(exclude_unset=True)

    if "categoria_id" in cambios:
        _validar_categoria(db, cambios["categoria_id"])

    if cambios.get("cantidad") is not None:
        comprometidas = item.cantidad_recibida + contar_reservas_activas(db, item.id)
        if cambios["cantidad"] < comprometidas:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Ya hay {comprometidas} unidades recibidas o reservadas: "
                    "no se puede bajar la cantidad por debajo de ese número."
                ),
            )

    for campo, valor in cambios.items():
        setattr(item, campo, valor)
    recalcular_item(db, item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}/reservas", response_model=list[ReservaAdminOut])
def listar_reservas(
    item_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Reservas activas del item. Nunca incluye nombre ni mensaje: el admin
    solo ve cuántas hay y hace cuánto, para decidir si liberar alguna."""
    _get_item_or_404(item_id, db)
    ahora = datetime.now(UTC)
    return [
        ReservaAdminOut(
            id=r.id,
            unidad=r.unidad,
            dias_desde_reserva=(ahora - r.created_at).days,
        )
        for r in reservas_activas(db, item_id)
    ]


@router.post(
    "/{item_id}/reservas/{reserva_id}/recibir", response_model=ReservaReveladaOut
)
def recibir_unidad(
    item_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Marca recibida esa unidad y revela quién la regaló. Las otras
    reservas del mismo item siguen ocultas."""
    item = _get_item_or_404(item_id, db)
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.id == reserva_id,
            Reserva.item_id == item_id,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva activa no encontrada")

    reserva.revelado = True
    reserva.released_at = datetime.now(UTC)
    # La promesa se convierte en un hecho: la reserva queda cerrada y nace
    # el regalo, con el nombre y el mensaje que había dejado la persona.
    db.add(
        Regalo(
            item_id=item.id,
            persona=reserva.nombre_reservante,
            origen=OrigenRegalo.REGALO,
            cantidad=1,
            fecha=datetime.now(UTC).date(),
            nota=reserva.mensaje,
            reserva_id=reserva.id,
        )
    )
    recalcular_item(db, item)
    db.commit()
    db.refresh(item)
    return ReservaReveladaOut(
        nombre=reserva.nombre_reservante, mensaje=reserva.mensaje, item=item
    )


@router.post("/{item_id}/reservas/{reserva_id}/liberar", response_model=ItemOut)
def liberar_unidad(
    item_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Descarta la reserva sin revelar nada: la unidad vuelve a estar
    disponible y el nombre nunca sale de la tabla reservas."""
    item = _get_item_or_404(item_id, db)
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.id == reserva_id,
            Reserva.item_id == item_id,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva activa no encontrada")

    reserva.released_at = datetime.now(UTC)
    recalcular_item(db, item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/adquirir", response_model=ItemOut)
def adquirir_item(
    item_id: int,
    body: ItemAdquirir,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Recibe todas las unidades que falten como compra propia o regalo
    cargado a mano. Si hay reservas activas hay que resolverlas primero."""
    item = _get_item_or_404(item_id, db)

    if item.estado == EstadoItem.ADQUIRIDO:
        raise HTTPException(status_code=409, detail="El item ya está adquirido")

    if contar_reservas_activas(db, item.id) > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "El item tiene unidades reservadas. Recibí o liberá esas "
                "reservas antes de marcarlo por tu cuenta."
            ),
        )

    faltantes = item.cantidad - item.cantidad_recibida
    # Regalo y préstamo necesitan saber de quién vino; lo comprado, no.
    # En el préstamo la persona importa todavía más: hay que devolvérselo.
    origen_regalo = OrigenRegalo[body.origen.value]
    lleva_persona = origen_regalo in (OrigenRegalo.REGALO, OrigenRegalo.PRESTADO)
    db.add(
        Regalo(
            item_id=item.id,
            persona=(body.gifter_name or "").strip() if lleva_persona else "",
            origen=origen_regalo,
            cantidad=faltantes,
            fecha=datetime.now(UTC).date(),
        )
    )
    recalcular_item(db, item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = _get_item_or_404(item_id, db)
    if contar_reservas_activas(db, item.id) > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "El item tiene unidades reservadas. Liberá esas reservas "
                "primero para poder eliminarlo."
            ),
        )
    # Las fotos en DB caen por cascade; los objetos del storage se borran aquí.
    if storage.esta_configurado():
        for foto in item.fotos:
            key = storage.key_desde_url(foto.url)
            if key:
                storage.borrar_objeto(key)
    db.delete(item)
    db.commit()
