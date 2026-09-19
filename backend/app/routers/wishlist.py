from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.ratelimit import limiter
from app.models.admin import Admin
from app.models.item import EstadoItem, Item, Prioridad
from app.models.regalo import OrigenRegalo, Regalo
from app.models.reserva import Reserva
from app.models.wishlist_config import WishlistConfig
from app.schemas.wishlist import (
    ConfigOut,
    ConfigUpdate,
    ItemPublicoOut,
    RegaloPublicoOut,
    ReservaPendienteOut,
    ReservarRequest,
    ReservarResponse,
    ReservasCountOut,
    WishlistLinkOut,
    WishlistPublicaOut,
)
from app.services.items import (
    primera_unidad_libre,
    recalcular_estado,
    unidades_disponibles,
)

router = APIRouter(tags=["wishlist"])

# Los urgentes primero en la vista pública.
_ORDEN_PRIORIDAD = case(
    (Item.prioridad == Prioridad.URGENTE, 0),
    (Item.prioridad == Prioridad.NORMAL, 1),
    else_=2,
)


def _get_config(db: Session) -> WishlistConfig:
    config = db.query(WishlistConfig).first()
    if not config:
        # La migración seed la crea; esto es solo red de seguridad.
        config = WishlistConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# --- Config (nombre de la app) ---


@router.get("/config", response_model=ConfigOut)
@limiter.limit("30/minute")
def obtener_config(request: Request, db: Session = Depends(get_db)):
    return ConfigOut.model_validate(_get_config(db))


@router.patch("/config", response_model=ConfigOut)
def actualizar_config(
    body: ConfigUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    config = _get_config(db)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        if valor is None:
            continue
        limpio = valor.strip()
        # Vacío borra el dato; en nombre_app no aplica porque el schema
        # ya exige al menos un carácter.
        setattr(config, campo, limpio or None)
    db.commit()
    db.refresh(config)
    return ConfigOut.model_validate(config)


# --- Link compartible (admin) ---


@router.get("/wishlist/link", response_model=WishlistLinkOut)
def obtener_link(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return WishlistLinkOut(share_token=_get_config(db).share_token)


# --- Contador de actividad (admin, sin nombres) ---


@router.get("/reservas/pendientes/count", response_model=ReservasCountOut)
def contar_reservas_pendientes(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    pendientes = db.query(Reserva).filter(Reserva.released_at.is_(None)).count()
    return ReservasCountOut(pendientes=pendientes)


@router.get("/reservas/pendientes", response_model=list[ReservaPendienteOut])
def listar_reservas_pendientes(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Todo lo que está en camino, de todos los items, en un solo lugar.

    Incluye el nombre del objeto para poder encontrarlo cuando llega, pero
    nunca el de quien lo reservó: eso se revela recién al recibirlo.
    """
    ahora = datetime.now(UTC)
    reservas = (
        db.query(Reserva)
        .options(selectinload(Reserva.item))
        .filter(Reserva.released_at.is_(None))
        .order_by(Reserva.created_at)
        .all()
    )
    return [
        ReservaPendienteOut(
            id=r.id,
            item_id=r.item_id,
            item_nombre=r.item.nombre,
            unidad=r.unidad,
            total_unidades=r.item.cantidad,
            dias_desde_reserva=(ahora - r.created_at).days,
        )
        for r in reservas
    ]


# --- Wishlist pública ---
#
# Liberar y recibir unidades vive en routers/items.py, porque ahora es por
# reserva individual (POST /items/{id}/reservas/{id}/liberar|recibir).


def _get_config_por_token(share_token: str, db: Session) -> WishlistConfig:
    config = (
        db.query(WishlistConfig)
        .filter(WishlistConfig.share_token == share_token)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Wishlist no encontrada")
    return config


@router.get("/w/{share_token}", response_model=WishlistPublicaOut)
@limiter.limit("30/minute")
def ver_wishlist(request: Request, share_token: str, db: Session = Depends(get_db)):
    config = _get_config_por_token(share_token, db)
    items = (
        db.query(Item)
        .options(selectinload(Item.fotos), selectinload(Item.categoria))
        .filter(Item.estado == EstadoItem.NECESITADO)
        .order_by(_ORDEN_PRIORIDAD, Item.created_at.desc())
        .all()
    )
    # Muro de agradecimiento: solo lo ya recibido de parte de alguien. Las
    # reservas pendientes todavía no son regalos, así que la sorpresa se
    # preserva sola por cómo quedó el modelo.
    recibidos = (
        db.query(Regalo)
        .options(selectinload(Regalo.fotos), selectinload(Regalo.item))
        .filter(Regalo.origen == OrigenRegalo.REGALO, Regalo.persona != "")
        .order_by(Regalo.fecha.desc(), Regalo.id.desc())
        .all()
    )

    return WishlistPublicaOut(
        nombre_app=config.nombre_app,
        items=[
            ItemPublicoOut(
                id=i.id,
                nombre=i.nombre,
                descripcion=i.descripcion,
                amazon_link=i.amazon_link,
                cantidad=i.cantidad,
                disponibles=unidades_disponibles(db, i),
                prioridad=i.prioridad,
                rango_precio=i.rango_precio,
                categoria=i.categoria.nombre if i.categoria else None,
                fotos=i.fotos,
            )
            for i in items
        ],
        recibidos=[
            RegaloPublicoOut(
                id=r.id,
                item=r.item.nombre,
                persona=r.persona,
                # La foto de Nicole usándolo es la que cuenta la historia;
                # si no hay, se cae a la de referencia del catálogo.
                foto=(
                    r.fotos[0].url
                    if r.fotos
                    else (r.item.fotos[0].url if r.item.fotos else None)
                ),
            )
            for r in recibidos
        ],
    )


@router.post(
    "/w/{share_token}/items/{item_id}/reservar",
    response_model=ReservarResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def reservar_item(
    request: Request,
    share_token: str,
    item_id: int,
    body: ReservarRequest,
    db: Session = Depends(get_db),
):
    _get_config_por_token(share_token, db)
    # FOR UPDATE serializa las reservas del mismo item: el chequeo de
    # disponibilidad y la asignación de unidad ocurren sin carreras.
    item = db.query(Item).filter(Item.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if unidades_disponibles(db, item) < 1:
        raise HTTPException(status_code=409, detail="El item ya no está disponible")

    reserva = Reserva(
        item_id=item_id,
        unidad=primera_unidad_libre(db, item_id),
        nombre_reservante=body.nombre.strip(),
        mensaje=(body.mensaje or "").strip() or None,
    )
    db.add(reserva)
    db.flush()
    recalcular_estado(db, item)
    try:
        db.commit()
    except IntegrityError as e:
        # Índice único parcial: segunda línea de defensa si el lock no
        # alcanzó (por ejemplo, con otro nivel de aislamiento).
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El item ya no está disponible"
        ) from e
    return ReservarResponse(
        token_deshacer=reserva.token_deshacer, unidad=reserva.unidad
    )


@router.post("/w/reservas/{token_deshacer}/deshacer", response_model=ConfigOut)
@limiter.limit("10/minute")
def deshacer_reserva(
    request: Request, token_deshacer: str, db: Session = Depends(get_db)
):
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.token_deshacer == token_deshacer,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    item = db.query(Item).filter(Item.id == reserva.item_id).first()
    reserva.released_at = datetime.now(UTC)
    db.flush()
    if item:
        recalcular_estado(db, item)
    db.commit()
    return ConfigOut(nombre_app=_get_config(db).nombre_app)
