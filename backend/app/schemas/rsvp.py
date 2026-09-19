from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RsvpCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    asistira: bool
    # Mensaje para Nicole, para leerle después.
    cantidad: str | None = Field(default=None, max_length=255)
    comentario: str | None = Field(default=None, max_length=2000)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("Hace falta un nombre")
        return limpio

    @field_validator("cantidad", "comentario")
    @classmethod
    def vacio_es_nada(cls, v: str | None) -> str | None:
        return (v or "").strip() or None


class RsvpUpdate(BaseModel):
    """Cambio de la propia respuesta. Todo opcional: se manda lo que cambia."""

    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    asistira: bool | None = None
    cantidad: str | None = Field(default=None, max_length=255)
    comentario: str | None = Field(default=None, max_length=2000)


class RsvpOut(BaseModel):
    id: int
    invitacion_id: int
    nombre: str
    asistira: bool
    cantidad: str | None = None
    comentario: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RsvpCreadoOut(RsvpOut):
    """Lo que ve quien acaba de responder: incluye su token para editar."""

    token_edicion: str


class ResumenRsvp(BaseModel):
    """Lo que se ve de un vistazo en el admin."""

    asisten: int
    no_asisten: int
    respuestas: list[RsvpOut]
