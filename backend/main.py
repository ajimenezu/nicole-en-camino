from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.ratelimit import limiter
from app.routers import (
    auth,
    cajas,
    categorias,
    fotos,
    invitaciones,
    items,
    regalos,
    rsvp,
    wishlist,
)

app = FastAPI(
    title="Nicole en Camino API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    # Apagar docs y redoc solo esconde las dos interfaces: el esquema
    # sigue sirviéndose en /openapi.json, que es de donde salen. Sin esta
    # línea, la superficie completa de la API quedaba pública.
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    """Cabeceras defensivas en toda respuesta de la API.

    `setdefault` y no asignación directa: si alguna respuesta ya trae la
    suya (hoy ninguna, pero es la clase de cosa que aparece después), no
    se la pisa.

    La CSP solo se aplica fuera de DEBUG porque en local `/docs` carga
    Swagger desde un CDN y `default-src 'none'` lo dejaría en blanco. La
    API no sirve HTML propio, así que fuera de local puede ser máxima.
    """
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    respuesta.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    if not settings.DEBUG:
        respuesta.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    return respuesta


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# Handler genérico para no filtrar stack traces al cliente.
# Nota: los exception_handlers de FastAPI pueden bypassear el CORSMiddleware,
# por eso añadimos manualmente el header Access-Control-Allow-Origin aquí.
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging

    logging.getLogger("nicole").error(f"Unhandled error: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    headers: dict[str, str] = {}
    if origin in settings.cors_origins_list:
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-credentials"] = "true"
        headers["vary"] = "Origin"
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
        headers=headers,
    )


app.include_router(auth.router)
app.include_router(items.router)
app.include_router(cajas.router)
app.include_router(cajas.items_router)
app.include_router(categorias.router)
app.include_router(fotos.router)
app.include_router(regalos.router)
app.include_router(invitaciones.router)
app.include_router(rsvp.router)
app.include_router(wishlist.router)


@app.get("/health")
def health():
    return {"status": "ok"}
