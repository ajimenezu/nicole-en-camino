import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

NOMBRE_APP_DEFAULT = "Nicole en Camino"


def _nuevo_share_token() -> str:
    return str(uuid.uuid4())


class WishlistConfig(Base):
    __tablename__ = "wishlist_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    share_token: Mapped[str] = mapped_column(
        String(36), unique=True, default=_nuevo_share_token
    )
    nombre_app: Mapped[str] = mapped_column(String(100), default=NOMBRE_APP_DEFAULT)
