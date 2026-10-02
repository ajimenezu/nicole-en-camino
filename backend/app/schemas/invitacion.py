from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class InvitacionBase(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    lugar: str | None = Field(default=None, max_length=255)
    fecha: str | None = Field(default=None, max_length=100)
    hora: str | None = Field(default=None, max_length=100)
    texto: str | None = Field(default=None, max_length=500)
    aviso: str | None = Field(default=None, max_length=500)

    @field_validator("titulo")
    @classmethod
    def titulo_no_vacio(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("La invitación necesita un título")
        return limpio


class InvitacionCreate(InvitacionBase):
    pide_cantidad: bool = False
    muestra_wishlist: bool = True


class InvitacionUpdate(BaseModel):
    """Solo lo que cambia. Un string vacío borra el dato."""

    titulo: str | None = Field(default=None, min_length=1, max_length=150)
    lugar: str | None = Field(default=None, max_length=255)
    fecha: str | None = Field(default=None, max_length=100)
    hora: str | None = Field(default=None, max_length=100)
    texto: str | None = Field(default=None, max_length=500)
    aviso: str | None = Field(default=None, max_length=500)
    pide_cantidad: bool | None = None
    muestra_wishlist: bool | None = None


class InvitacionAdminOut(BaseModel):
    """Vista del admin: incluye el título y cuántos respondieron."""

    id: int
    token: str
    titulo: str
    lugar: str | None = None
    fecha: str | None = None
    hora: str | None = None
    texto: str | None = None
    aviso: str | None = None
    imagen_url: str | None = None
    pide_cantidad: bool = False
    muestra_wishlist: bool = True
    asisten: int = 0
    no_asisten: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class InvitacionPublicaOut(BaseModel):
    """Lo que ve quien recibe el link. Sin el título, que es interno.

    `wishlist_token` viene solo si el evento lleva a la lista de regalos:
    es el link de la wishlist, y mandarlo igual cuando está apagado sería
    repartirlo de todas formas.
    """

    nombre_app: str
    lugar: str | None = None
    fecha: str | None = None
    hora: str | None = None
    texto: str | None = None
    aviso: str | None = None
    imagen_url: str | None = None
    pide_cantidad: bool = False
    wishlist_token: str | None = None
