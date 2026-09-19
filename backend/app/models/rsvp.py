import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_token() -> str:
    return str(uuid.uuid4())


class Rsvp(Base):
    """Confirmación de asistencia a una invitación.

    Se guarda cada respuesta tal como llega, sin cuenta ni identidad: la
    invitación se comparte por link. Que alguien responda dos veces es
    posible y no se bloquea — corregirlo desde el admin es más simple que
    adivinar si «Ana» y «Ana Pérez» son la misma persona.
    """

    __tablename__ = "rsvps"

    id: Mapped[int] = mapped_column(primary_key=True)
    invitacion_id: Mapped[int] = mapped_column(
        ForeignKey("invitaciones.id", ondelete="CASCADE"), index=True
    )
    # Credencial para editar la propia respuesta desde el navegador que
    # la creó, igual que el token_deshacer de las reservas. Sin esto,
    # cambiar de opinión dejaba la respuesta vieja viva y creaba otra.
    token_edicion: Mapped[str] = mapped_column(
        String(36), unique=True, default=_nuevo_token
    )
    nombre: Mapped[str] = mapped_column(String(255))
    asistira: Mapped[bool] = mapped_column(Boolean, default=True)
    # Cuántos vienen, como texto y no como número: «2 adultos y 1 bebé»
    # dice más que un 3, y quien invita a una familia quiere saber eso.
    cantidad: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Mensaje para Nicole. Es lo que se guarda para leerle después, así
    # que va sin tope corto y como texto libre.
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    invitacion = relationship("Invitacion", back_populates="rsvps")
