from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.core import storage_r2
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.regalo import FotoRegalo, OrigenRegalo, Regalo
from app.schemas.foto import FotoConfirmar, PresignRequest, PresignResponse
from app.schemas.regalo import (
    DevolucionCreate,
    FotoRegaloOut,
    RegaloCreate,
    RegaloOut,
    RegalosDePersonaOut,
    RegaloUpdate,
)
from app.services.items import recalcular_item

router = APIRouter(prefix="/regalos", tags=["regalos"])


def _cargado(query):
    return query.options(
        selectinload(Regalo.fotos),
        selectinload(Regalo.item).selectinload(Item.fotos),
    )


def _get_regalo_or_404(regalo_id: int, db: Session) -> Regalo:
    regalo = _cargado(db.query(Regalo)).filter(Regalo.id == regalo_id).first()
    if not regalo:
        raise HTTPException(status_code=404, detail="Regalo no encontrado")
    return regalo


@router.post("", response_model=RegaloOut, status_code=status.HTTP_201_CREATED)
def registrar_regalo(
    body: RegaloCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Registra 'recibimos X de parte de Y' en un solo paso.

    Si el objeto no existe todavía se crea acá mismo: la mayoría de los
    regalos llegan sin haber pasado por la wishlist.
    """
    if body.item_nuevo is not None:
        if body.item_nuevo.categoria_id is not None:
            existe = (
                db.query(Categoria)
                .filter(Categoria.id == body.item_nuevo.categoria_id)
                .first()
            )
            if not existe:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
        item = Item(**body.item_nuevo.model_dump(), cantidad=body.cantidad)
        db.add(item)
        db.flush()
    else:
        item = db.query(Item).filter(Item.id == body.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")

    regalo = Regalo(
        item_id=item.id,
        persona=body.persona.strip(),
        origen=body.origen,
        cantidad=body.cantidad,
        fecha=body.fecha or datetime.now(UTC).date(),
        nota=(body.nota or "").strip() or None,
    )
    db.add(regalo)
    recalcular_item(db, item)
    db.commit()
    return _get_regalo_or_404(regalo.id, db)


@router.get("", response_model=list[RegaloOut])
def listar_regalos(
    persona: str | None = None,
    agradecido: bool | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = _cargado(db.query(Regalo))
    if persona:
        query = query.filter(Regalo.persona == persona)
    if agradecido is not None:
        query = query.filter(Regalo.agradecido.is_(agradecido))
    if desde:
        query = query.filter(Regalo.fecha >= desde)
    if hasta:
        query = query.filter(Regalo.fecha <= hasta)
    return query.order_by(Regalo.fecha.desc(), Regalo.id.desc()).all()


@router.get("/personas", response_model=list[str])
def listar_personas(
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Nombres ya usados, para el autocompletado.

    Es lo que mantiene consistente el texto libre: si Ana ya existe, se
    elige de la lista en vez de volver a escribirla distinto.
    """
    query = db.query(Regalo.persona).filter(Regalo.persona != "").distinct()
    if q:
        query = query.filter(Regalo.persona.ilike(f"%{q.strip()}%"))
    return sorted(p[0] for p in query.all())


@router.get("/por-persona", response_model=list[RegalosDePersonaOut])
def regalos_por_persona(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Lo que regaló cada persona, para agradecer sin olvidarse de nadie."""
    regalos = (
        _cargado(db.query(Regalo))
        .filter(Regalo.persona != "")
        .order_by(Regalo.persona, Regalo.fecha)
        .all()
    )
    agrupados: dict[str, list[Regalo]] = {}
    for regalo in regalos:
        agrupados.setdefault(regalo.persona, []).append(regalo)

    return [
        RegalosDePersonaOut(
            persona=persona,
            total_regalos=len(items),
            pendientes_de_agradecer=sum(1 for r in items if not r.agradecido),
            regalos=[RegaloOut.model_validate(r) for r in items],
        )
        for persona, items in agrupados.items()
    ]


@router.patch("/{regalo_id}", response_model=RegaloOut)
def editar_regalo(
    regalo_id: int,
    body: RegaloUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    regalo = _get_regalo_or_404(regalo_id, db)
    cambios = body.model_dump(exclude_unset=True)
    if "persona" in cambios and cambios["persona"] is not None:
        cambios["persona"] = cambios["persona"].strip()
        if not cambios["persona"] and regalo.origen in (
            OrigenRegalo.REGALO,
            OrigenRegalo.PRESTADO,
        ):
            raise HTTPException(
                status_code=422,
                detail="Hace falta el nombre de quien lo dio",
            )
    for campo, valor in cambios.items():
        setattr(regalo, campo, valor)
    recalcular_item(db, regalo.item)
    db.commit()
    return _get_regalo_or_404(regalo_id, db)


@router.post("/{regalo_id}/devolucion", response_model=RegaloOut)
def marcar_devuelto(
    regalo_id: int,
    body: DevolucionCreate | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Registra que le devolvimos el objeto a quien lo prestó.

    No libera la unidad ni baja cantidad_recibida: el objeto ya cumplió su
    función y revivir la necesidad volvería a publicarlo en la lista
    pública, donde alguien podría comprarlo sin que haga falta.
    """
    regalo = _get_regalo_or_404(regalo_id, db)
    if regalo.origen != OrigenRegalo.PRESTADO:
        raise HTTPException(
            status_code=422,
            detail="Solo se devuelve lo que nos prestaron",
        )
    regalo.devuelto_en = (body.devuelto_en if body else None) or datetime.now(
        UTC
    ).date()
    db.commit()
    return _get_regalo_or_404(regalo_id, db)


@router.delete("/{regalo_id}/devolucion", response_model=RegaloOut)
def deshacer_devolucion(
    regalo_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Deshace la marca de devuelto, para cuando se marcó por error."""
    regalo = _get_regalo_or_404(regalo_id, db)
    regalo.devuelto_en = None
    db.commit()
    return _get_regalo_or_404(regalo_id, db)


@router.delete("/{regalo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_regalo(
    regalo_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    regalo = _get_regalo_or_404(regalo_id, db)
    item = regalo.item
    if storage_r2.esta_configurado():
        for foto in regalo.fotos:
            key = storage_r2.key_desde_url(foto.url)
            if key:
                storage_r2.borrar_objeto(key)
    db.delete(regalo)
    recalcular_item(db, item)
    db.commit()


# --- Fotos de Nicole usando el regalo ---


def _check_r2():
    if not storage_r2.esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Storage de fotos no configurado (variables R2_* faltantes)",
        )


@router.post("/{regalo_id}/fotos/presign", response_model=PresignResponse)
def presign_foto(
    regalo_id: int,
    body: PresignRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_r2()
    _get_regalo_or_404(regalo_id, db)
    if body.content_type not in storage_r2.CONTENT_TYPES_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail="Tipo de archivo no permitido (solo jpeg, png, webp)",
        )
    if body.size_bytes > storage_r2.MAX_BYTES:
        raise HTTPException(
            status_code=422, detail="La foto supera el tamaño máximo de 5 MB"
        )
    key = storage_r2.generar_key(regalo_id, body.content_type, prefijo="regalos")
    return PresignResponse(
        upload_url=storage_r2.presign_put(key, body.content_type), key=key
    )


@router.post(
    "/{regalo_id}/fotos",
    response_model=FotoRegaloOut,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_foto(
    regalo_id: int,
    body: FotoConfirmar,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_r2()
    _get_regalo_or_404(regalo_id, db)
    if not storage_r2.key_pertenece_a_item(body.key, regalo_id, prefijo="regalos"):
        raise HTTPException(
            status_code=422,
            detail="La key no corresponde a un presign emitido para este regalo",
        )
    if not storage_r2.objeto_existe(body.key):
        raise HTTPException(
            status_code=422,
            detail="El archivo no existe en el storage (¿falló la subida?)",
        )
    foto = FotoRegalo(
        regalo_id=regalo_id, url=storage_r2.url_publica(body.key), orden=body.orden
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


@router.delete("/{regalo_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto(
    regalo_id: int,
    foto_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    foto = (
        db.query(FotoRegalo)
        .filter(FotoRegalo.id == foto_id, FotoRegalo.regalo_id == regalo_id)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    if storage_r2.esta_configurado():
        key = storage_r2.key_desde_url(foto.url)
        if key:
            storage_r2.borrar_objeto(key)
    db.delete(foto)
    db.commit()
