import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

if os.environ.get("VERCEL"):
    # En Vercel puede haber muchas instancias de la función a la vez y
    # cualquiera se apaga sin aviso: un pool propio en cada una solo
    # acumula conexiones abiertas contra Postgres. Ahí el pool lo pone
    # Supabase (el pooler en modo transacción, puerto 6543), así que la
    # app abre una conexión por pedido y la suelta al terminar.
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
else:
    # pre_ping descarta la conexión que el servidor cerró por inactividad
    # antes de usarla, en vez de fallar el primer pedido después de un rato.
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
