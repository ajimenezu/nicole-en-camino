import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import imagen_remota, storage
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.item import FotoItem, Item
from app.schemas.foto import (
    FotoConfirmar,
    FotoDesdeUrl,
    PresignRequest,
    PresignResponse,
)
from app.schemas.item import FotoItemOut

router = APIRouter(prefix="/items", tags=["fotos"])


def _get_item_or_404(item_id: int, db: Session) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


def _check_storage():
    if not storage.esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Storage de fotos no configurado (variables STORAGE_* faltantes)",
        )


@router.post("/{item_id}/fotos/presign", response_model=PresignResponse)
def presign_foto(
    item_id: int,
    body: PresignRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_storage()
    _get_item_or_404(item_id, db)
    if body.content_type not in storage.CONTENT_TYPES_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail="Tipo de archivo no permitido (solo jpeg, png, webp)",
        )
    if body.size_bytes > storage.MAX_BYTES:
        raise HTTPException(
            status_code=422,
            detail="La foto supera el tamaño máximo de 5 MB",
        )
    key = storage.generar_key(item_id, body.content_type)
    url = storage.presign_put(key, body.content_type)
    return PresignResponse(upload_url=url, key=key)


@router.post(
    "/{item_id}/fotos",
    response_model=FotoItemOut,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_foto(
    item_id: int,
    body: FotoConfirmar,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_storage()
    _get_item_or_404(item_id, db)
    if not storage.key_pertenece_a_item(body.key, item_id):
        raise HTTPException(
            status_code=422,
            detail="La key no corresponde a un presign emitido para este item",
        )
    if not storage.objeto_existe(body.key):
        raise HTTPException(
            status_code=422,
            detail="El archivo no existe en el storage (¿falló la subida?)",
        )
    foto = FotoItem(
        item_id=item_id, url=storage.url_publica(body.key), orden=body.orden
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


@router.post(
    "/{item_id}/fotos/desde-url",
    response_model=FotoItemOut,
    status_code=status.HTTP_201_CREATED,
)
def foto_desde_url(
    item_id: int,
    body: FotoDesdeUrl,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Importa la imagen del producto desde el link de la tienda."""
    _check_storage()
    _get_item_or_404(item_id, db)
    try:
        contenido, content_type = imagen_remota.obtener_imagen(str(body.url))
    except imagen_remota.ImagenRemotaError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=422, detail="No se pudo abrir ese link") from e

    key = storage.generar_key(item_id, content_type)
    storage.subir_bytes(key, contenido, content_type)
    foto = FotoItem(item_id=item_id, url=storage.url_publica(key), orden=body.orden)
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


@router.delete("/{item_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto(
    item_id: int,
    foto_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    foto = (
        db.query(FotoItem)
        .filter(FotoItem.id == foto_id, FotoItem.item_id == item_id)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    if storage.esta_configurado():
        key = storage.key_desde_url(foto.url)
        if key:
            storage.borrar_objeto(key)
    db.delete(foto)
    db.commit()
