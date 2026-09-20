"""Invitaciones: varios eventos, cada uno con su link y su lámina."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from app.core import storage
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.ratelimit import limiter
from app.models.admin import Admin
from app.models.invitacion import Invitacion
from app.models.wishlist_config import WishlistConfig
from app.schemas.foto import FotoConfirmar, PresignRequest, PresignResponse
from app.schemas.invitacion import (
    InvitacionAdminOut,
    InvitacionCreate,
    InvitacionPublicaOut,
    InvitacionUpdate,
)

router = APIRouter(tags=["invitaciones"])


def _get_or_404(invitacion_id: int, db: Session) -> Invitacion:
    inv = db.query(Invitacion).filter(Invitacion.id == invitacion_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    return inv


def _con_totales(inv: Invitacion) -> InvitacionAdminOut:
    salida = InvitacionAdminOut.model_validate(inv)
    salida.asisten = sum(1 for r in inv.rsvps if r.asistira)
    salida.no_asisten = sum(1 for r in inv.rsvps if not r.asistira)
    return salida


# --- Admin ---


@router.get("/invitaciones", response_model=list[InvitacionAdminOut])
def listar(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    invitaciones = (
        db.query(Invitacion)
        .options(selectinload(Invitacion.rsvps))
        .order_by(Invitacion.created_at.desc())
        .all()
    )
    return [_con_totales(i) for i in invitaciones]


@router.post(
    "/invitaciones",
    response_model=InvitacionAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def crear(
    body: InvitacionCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    inv = Invitacion(**body.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _con_totales(inv)


@router.patch("/invitaciones/{invitacion_id}", response_model=InvitacionAdminOut)
def editar(
    invitacion_id: int,
    body: InvitacionUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    inv = _get_or_404(invitacion_id, db)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        if valor is None:
            continue
        if isinstance(valor, bool):
            setattr(inv, campo, valor)
            continue
        # Vacío borra el dato; el título no puede quedar vacío porque el
        # schema ya exige al menos un carácter.
        setattr(inv, campo, valor.strip() or None)
    db.commit()
    db.refresh(inv)
    return _con_totales(inv)


@router.delete("/invitaciones/{invitacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    invitacion_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Se lleva sus confirmaciones: son de ese evento y de ningún otro."""
    inv = _get_or_404(invitacion_id, db)
    if inv.imagen_url and storage.esta_configurado():
        key = storage.key_desde_url(inv.imagen_url)
        if key:
            storage.borrar_objeto(key)
    db.delete(inv)
    db.commit()


# --- Lámina propia ---


@router.post(
    "/invitaciones/{invitacion_id}/imagen/presign", response_model=PresignResponse
)
def presign_imagen(
    invitacion_id: int,
    body: PresignRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    if not storage.esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Storage de fotos no configurado (variables STORAGE_* faltantes)",
        )
    _get_or_404(invitacion_id, db)
    if body.content_type not in storage.CONTENT_TYPES_PERMITIDOS:
        raise HTTPException(
            status_code=422, detail="Tipo de archivo no permitido (jpeg, png, webp)"
        )
    if body.size_bytes > storage.MAX_BYTES:
        raise HTTPException(
            status_code=422, detail="La imagen supera el tamaño máximo de 5 MB"
        )
    key = storage.generar_key(invitacion_id, body.content_type, prefijo="invitaciones")
    return PresignResponse(
        upload_url=storage.presign_put(key, body.content_type), key=key
    )


@router.post("/invitaciones/{invitacion_id}/imagen", response_model=InvitacionAdminOut)
def confirmar_imagen(
    invitacion_id: int,
    body: FotoConfirmar,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    inv = _get_or_404(invitacion_id, db)
    if not storage.key_pertenece_a_item(
        body.key, invitacion_id, prefijo="invitaciones"
    ):
        raise HTTPException(
            status_code=422,
            detail="La key no corresponde a un presign de esta invitación",
        )
    anterior = inv.imagen_url
    inv.imagen_url = storage.url_publica(body.key)
    db.commit()
    # La lámina vieja ya no la referencia nadie.
    if anterior:
        key = storage.key_desde_url(anterior)
        if key:
            storage.borrar_objeto(key)
    db.refresh(inv)
    return _con_totales(inv)


@router.delete(
    "/invitaciones/{invitacion_id}/imagen", response_model=InvitacionAdminOut
)
def quitar_imagen(
    invitacion_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Vuelve a la lámina que viene con la app."""
    inv = _get_or_404(invitacion_id, db)
    if inv.imagen_url and storage.esta_configurado():
        key = storage.key_desde_url(inv.imagen_url)
        if key:
            storage.borrar_objeto(key)
    inv.imagen_url = None
    db.commit()
    db.refresh(inv)
    return _con_totales(inv)


# --- Pública ---


@router.get("/i/{token}", response_model=InvitacionPublicaOut)
@limiter.limit("30/minute")
def ver_invitacion(request: Request, token: str, db: Session = Depends(get_db)):
    inv = db.query(Invitacion).filter(Invitacion.token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Link no válido")
    config = db.query(WishlistConfig).first()
    return InvitacionPublicaOut(
        nombre_app=config.nombre_app if config else "Nicole en Camino",
        lugar=inv.lugar,
        fecha=inv.fecha,
        hora=inv.hora,
        texto=inv.texto,
        aviso=inv.aviso,
        imagen_url=inv.imagen_url,
        pide_cantidad=inv.pide_cantidad,
    )
