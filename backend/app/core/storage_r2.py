"""Cliente S3-compatible para Cloudflare R2.

Flujo: el backend genera una URL presignada de PUT restringida a
content-type de imagen y tamaño máximo; el frontend sube directo a R2 y
luego confirma. Las keys siguen el patrón items/{item_id}/{uuid}.{ext},
lo que permite validar en la confirmación que la key pertenece al item.
"""

import re
import uuid

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import settings

CONTENT_TYPES_PERMITIDOS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# Tres colecciones: fotos de referencia del catálogo (items/), fotos de
# Nicole usando cada regalo (regalos/) y las láminas de invitación
# (invitaciones/).
_KEY_RE = re.compile(
    r"^(items|regalos|invitaciones)/(\d+)/[0-9a-f-]{36}\.(jpg|png|webp)$"
)


def esta_configurado() -> bool:
    return bool(
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
        and settings.R2_BUCKET
    )


def _cliente():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def generar_key(item_id: int, content_type: str, prefijo: str = "items") -> str:
    ext = CONTENT_TYPES_PERMITIDOS[content_type]
    return f"{prefijo}/{item_id}/{uuid.uuid4()}.{ext}"


def key_pertenece_a_item(key: str, item_id: int, prefijo: str = "items") -> bool:
    """Valida que la key corresponda a un presign emitido para ese dueño."""
    m = _KEY_RE.match(key)
    return bool(m) and m.group(1) == prefijo and int(m.group(2)) == item_id


def presign_put(key: str, content_type: str) -> str:
    return _cliente().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=600,
    )


def subir_bytes(key: str, contenido: bytes, content_type: str) -> None:
    """Sube desde el backend, sin presign.

    Lo usa la importación de imágenes desde el link de la tienda: ahí el
    archivo ya está en memoria del servidor y no tiene sentido darle una
    vuelta por el navegador.
    """
    _cliente().put_object(
        Bucket=settings.R2_BUCKET,
        Key=key,
        Body=contenido,
        ContentType=content_type,
    )


def objeto_existe(key: str) -> bool:
    try:
        _cliente().head_object(Bucket=settings.R2_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def borrar_objeto(key: str) -> None:
    try:
        _cliente().delete_object(Bucket=settings.R2_BUCKET, Key=key)
    except ClientError:
        # El borrado en R2 es best-effort: no bloqueamos la operación en DB
        # por un fallo transitorio del storage.
        pass


def url_publica(key: str) -> str:
    return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"


def key_desde_url(url: str) -> str | None:
    base = settings.R2_PUBLIC_URL.rstrip("/")
    if base and url.startswith(base + "/"):
        return url[len(base) + 1 :]
    return None
