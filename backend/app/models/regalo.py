import enum
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrigenRegalo(str, enum.Enum):
    REGALO = "REGALO"
    NOSOTROS = "NOSOTROS"
    # Prestado: como el regalo, necesita saber de quién vino, porque hay
    # que devolvérselo.
    PRESTADO = "PRESTADO"


class Regalo(Base):
    """El hecho: recibimos este objeto, de parte de esta persona.

    Reemplaza al viejo Item.gifter_name (que era un string concatenado y
    no permitía responder "¿qué nos regaló Ana?").
    """

    __tablename__ = "regalos"
    __table_args__ = (
        CheckConstraint("cantidad >= 1", name="ck_regalos_cantidad_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    # Texto libre; el frontend autocompleta con los nombres ya usados para
    # que no queden variantes de la misma persona. Vacío si lo compramos.
    persona: Mapped[str] = mapped_column(String(255), default="", index=True)
    origen: Mapped[OrigenRegalo] = mapped_column(
        Enum(OrigenRegalo), default=OrigenRegalo.REGALO
    )
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    fecha: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(UTC).date())
    nota: Mapped[str | None] = mapped_column(Text)
    agradecido: Mapped[bool] = mapped_column(Boolean, default=False)
    # Solo tiene sentido en los préstamos. Nulo mientras el objeto siga en
    # casa; con fecha, ya volvió a quien lo prestó.
    devuelto_en: Mapped[date | None] = mapped_column(Date)
    # Solo si llegó por la wishlist: enlaza con la reserva que lo originó.
    reserva_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservas.id", ondelete="SET NULL"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    item = relationship("Item", back_populates="regalos")
    fotos = relationship(
        "FotoRegalo",
        back_populates="regalo",
        cascade="all, delete-orphan",
        order_by="FotoRegalo.orden",
    )


class FotoRegalo(Base):
    """Foto de Nicole usando el regalo, para compartirle a quien lo dio.

    Cuelga del regalo y no del item: si dos personas regalaron lo mismo,
    cada una tiene su foto.
    """

    __tablename__ = "fotos_regalo"

    id: Mapped[int] = mapped_column(primary_key=True)
    regalo_id: Mapped[int] = mapped_column(
        ForeignKey("regalos.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(2000))
    orden: Mapped[int] = mapped_column(Integer, default=0)

    regalo = relationship("Regalo", back_populates="fotos")
