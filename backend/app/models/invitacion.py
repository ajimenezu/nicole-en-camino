import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_token() -> str:
    return str(uuid.uuid4())


class Invitacion(Base):
    """Un evento invitable, con su propio link, su lámina y sus datos.

    Nace de necesitar varios baby showers: cada tanda de invitados tiene
    su fecha, su lugar y su lista de confirmados, y mezclarlas haría
    inservible el conteo.

    El `titulo` es solo para el admin —para distinguirlas en la lista— y
    nunca se muestra a quien recibe el link.
    """

    __tablename__ = "invitaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(36), unique=True, default=_nuevo_token)
    titulo: Mapped[str] = mapped_column(String(150))

    lugar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hora: Mapped[str | None] = mapped_column(String(100), nullable=True)
    texto: Mapped[str | None] = mapped_column(String(500), nullable=True)
    aviso: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Si se pregunta cuántos vienen. Solo tiene sentido cuando se invita
    # a familias; en una tanda de amigas es un campo de más.
    pide_cantidad: Mapped[bool] = mapped_column(Boolean, default=False)

    # Si la invitación lleva al que la recibe hasta la lista de regalos.
    # Es por evento: a un baby shower se le pide lista, a una juntada de
    # amigas quizá no, y el link de la wishlist se reparte con quienes la
    # piden. Nace prendido, que es el caso común.
    muestra_wishlist: Mapped[bool] = mapped_column(Boolean, default=True)

    # Lámina propia. Si está vacía se usa la que viene con la app: sirve
    # para el caso más común, varias tandas del mismo baby shower.
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    rsvps = relationship(
        "Rsvp", back_populates="invitacion", cascade="all, delete-orphan"
    )
