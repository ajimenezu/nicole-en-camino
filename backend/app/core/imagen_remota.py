"""Saca la imagen de un producto a partir del link de la tienda.

Se busca `og:image`, la etiqueta que publica casi cualquier tienda para
que el link se vea bien al compartirlo en WhatsApp. Amazon es la
excepción justo en el caso que más nos importa: no expone Open Graph,
así que para sus páginas se cae a buscar las URLs de `m.media-amazon.com`
embebidas en el HTML. Ese camino es frágil por naturaleza y además
Amazon suele servir captcha a las IPs de datacenter, así que puede
fallar en producción aunque funcione en local.

Seguridad: la URL la elige quien entra al admin, pero el pedido sale
desde el servidor, y eso es un SSRF en potencia — alguien podría
apuntarlo a `169.254.169.254` o a un servicio interno de la red. Por
eso se valida el esquema y se resuelve el host contra rangos privados
**en cada salto** del redirect, no solo en la URL original.
"""

import ipaddress
import re
import socket
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

from app.core import storage

TIMEOUT = 10.0
MAX_REDIRECCIONES = 3

# Varias tiendas devuelven una página distinta (o directamente un
# captcha) si el user agent parece un script.
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# El atributo puede venir antes o después de content, así que hacen
# falta las dos variantes.
_META_IMAGEN = re.compile(
    r"""<meta[^>]+(?:property|name)=["'](?:og:image(?::secure_url)?|twitter:image)["']"""
    r"""[^>]+content=["']([^"']+)""",
    re.I,
)
_META_IMAGEN_INVERSO = re.compile(
    r"""<meta[^>]+content=["']([^"']+)["']"""
    r"""[^>]+(?:property|name)=["'](?:og:image(?::secure_url)?|twitter:image)["']""",
    re.I,
)
# Amazon sirve la misma imagen en decenas de tamaños, codificando el
# recorte en el nombre: <id>._AC_SX300_.jpg. Esas versiones son diez
# veces más frecuentes en el HTML que la desnuda, así que se aceptan las
# dos y después se arma la URL sin sufijo, que devuelve el original.
# Solo /images/I/ (fotos); /images/G/ son los sprites de la interfaz.
_IMAGEN_AMAZON = re.compile(
    r"https://m\.media-amazon\.com/images/I/([A-Za-z0-9_+-]{8,})"
    r"(?:\._[A-Za-z0-9_,]+_)?\.(jpg|png)",
    re.I,
)


class ImagenRemotaError(Exception):
    """No se pudo obtener una imagen usable de esa URL."""


def _host_es_publico(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return bool(infos)


def _validar_url(url: str) -> str:
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        raise ImagenRemotaError("Solo se admiten links http o https")
    if not _host_es_publico(partes.hostname):
        raise ImagenRemotaError("Ese link apunta a una dirección no pública")
    return url


def _descargar(
    cliente: httpx.Client, url: str, max_bytes: int
) -> tuple[bytes, str, str]:
    """Baja la URL siguiendo redirects a mano, validando cada salto.

    Devuelve (contenido, content_type, url_final). Corta la descarga en
    cuanto pasa de `max_bytes` en vez de confiar en Content-Length, que
    el otro lado puede omitir o mentir.
    """
    actual = _validar_url(url)
    for _ in range(MAX_REDIRECCIONES + 1):
        with cliente.stream(
            "GET", actual, headers={"User-Agent": _UA}, follow_redirects=False
        ) as respuesta:
            destino = respuesta.headers.get("location")
            if respuesta.is_redirect and destino:
                actual = _validar_url(urljoin(actual, destino))
                continue
            if respuesta.status_code >= 400:
                raise ImagenRemotaError(f"La tienda respondió {respuesta.status_code}")
            buffer = bytearray()
            for trozo in respuesta.iter_bytes():
                buffer.extend(trozo)
                if len(buffer) > max_bytes:
                    raise ImagenRemotaError(
                        "El archivo supera el tamaño máximo de 5 MB"
                    )
            tipo = respuesta.headers.get("content-type", "")
            tipo = tipo.split(";")[0].strip().lower()
            return bytes(buffer), tipo, actual
    raise ImagenRemotaError("El link da demasiadas vueltas (redirecciones)")


def buscar_imagen_en_html(html: str, base: str) -> str | None:
    """URL de la imagen principal declarada en el HTML, si la hay."""
    for patron in (_META_IMAGEN, _META_IMAGEN_INVERSO):
        encontrado = patron.search(html)
        if encontrado:
            return urljoin(base, unescape(encontrado.group(1)))
    encontrado = _IMAGEN_AMAZON.search(html)
    if encontrado:
        identificador, extension = encontrado.group(1), encontrado.group(2)
        return f"https://m.media-amazon.com/images/I/{identificador}.{extension}"
    return None


def obtener_imagen(url: str) -> tuple[bytes, str]:
    """Devuelve (contenido, content_type) de la imagen de ese link.

    Admite tanto el link de la página del producto como el de la imagen
    en sí, que es la salida cuando la tienda no declara nada útil y hay
    que copiar la dirección de la imagen a mano.
    """
    with httpx.Client(timeout=TIMEOUT) as cliente:
        contenido, tipo, url_final = _descargar(cliente, url, storage.MAX_BYTES)

        if tipo in storage.CONTENT_TYPES_PERMITIDOS:
            return contenido, tipo

        if "html" not in tipo:
            raise ImagenRemotaError(
                "Ese link no es una página de producto ni una imagen"
            )

        candidata = buscar_imagen_en_html(
            contenido.decode("utf-8", errors="ignore"), url_final
        )
        if not candidata:
            raise ImagenRemotaError(
                "No encontré la imagen en esa página. Probá copiando la "
                "dirección de la imagen directamente."
            )

        imagen, tipo_imagen, _ = _descargar(cliente, candidata, storage.MAX_BYTES)
        if tipo_imagen not in storage.CONTENT_TYPES_PERMITIDOS:
            raise ImagenRemotaError(
                "La imagen de esa página está en un formato no admitido"
            )
        return imagen, tipo_imagen
