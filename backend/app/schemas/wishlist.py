from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.item import Prioridad, RangoPrecio
from app.schemas.item import FotoItemOut


class ConfigOut(BaseModel):
    """Lo que necesita el armazón de la app. Público y sin token.

    El lugar y la hora del evento no van acá: se sirven solo contra el
    token de la invitación, así no quedan consultables por cualquiera que
    dé con la API. La fecha de parto sí, porque la cuenta regresiva es
    justamente una página para compartir.
    """

    nombre_app: str
    fecha_parto: date | None = None

    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    """Solo lo que cambia. `fecha_parto: null` borra la fecha y apaga la
    cuenta regresiva."""

    nombre_app: str | None = Field(default=None, min_length=1, max_length=100)
    fecha_parto: date | None = None

    @field_validator("nombre_app")
    @classmethod
    def nombre_no_vacio(cls, v: str | None) -> str | None:
        """min_length no alcanza: "   " lo pasa y después queda vacío al
        limpiarlo, y nombre_app no admite nulo en la base."""
        if v is None:
            return None
        limpio = v.strip()
        if not limpio:
            raise ValueError("La app necesita un nombre")
        return limpio


class WishlistLinkOut(BaseModel):
    share_token: str


class ItemPublicoOut(BaseModel):
    """Vista de invitado: sin estado interno, sin origen, sin nombres —
    solo lo necesario para elegir qué regalar."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    cantidad: int
    disponibles: int
    prioridad: Prioridad
    rango_precio: RangoPrecio | None = None
    categoria: str | None = None
    fotos: list[FotoItemOut] = []


class RegaloPublicoOut(BaseModel):
    """Una entrada del muro de agradecimiento.

    Solo lleva lo que se agradece en público: qué fue y de parte de quién.
    Las notas privadas del regalador no salen.
    """

    id: int
    item: str
    persona: str
    foto: str | None = None


class WishlistPublicaOut(BaseModel):
    nombre_app: str
    items: list[ItemPublicoOut]
    recibidos: list[RegaloPublicoOut] = []


class ReservarRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    mensaje: str | None = Field(default=None, max_length=500)


class ReservarResponse(BaseModel):
    token_deshacer: str
    unidad: int


class ReservasCountOut(BaseModel):
    pendientes: int


class ReservaPendienteOut(BaseModel):
    """Una reserva en camino, vista por el admin.

    Lleva el nombre del objeto para poder identificarlo cuando llega, pero
    nunca el de quien reservó: eso es la sorpresa.
    """

    id: int
    item_id: int
    item_nombre: str
    unidad: int
    total_unidades: int
    dias_desde_reserva: int
