from app.core.config import Settings


def _settings(url: str) -> Settings:
    return Settings(
        DATABASE_URL=url,
        JWT_SECRET="un-secreto-de-desarrollo-cualquiera",
        DEBUG=True,
        _env_file=None,
    )


def test_normaliza_el_esquema_postgres():
    """Varios proveedores entregan postgres://, que SQLAlchemy 2.0 ya no
    acepta."""
    s = _settings("postgres://user:pass@host:5432/db")
    assert s.DATABASE_URL.startswith("postgresql://")


def test_no_toca_una_url_ya_correcta():
    url = "postgresql://user:pass@host:5432/db"
    assert _settings(url).DATABASE_URL == url


def test_solo_reemplaza_el_esquema_no_el_resto():
    """Una contraseña que contenga 'postgres://' no debe alterarse."""
    s = _settings("postgres://user:postgres%3A%2F%2Fx@host:5432/db")
    assert s.DATABASE_URL == "postgresql://user:postgres%3A%2F%2Fx@host:5432/db"


def test_cors_origins_se_parte_en_lista():
    s = _settings("postgresql://x@h/d")
    s.CORS_ORIGINS = "https://uno.app, https://dos.app"
    assert s.cors_origins_list == ["https://uno.app", "https://dos.app"]


def test_usa_postgres_url_de_la_integracion_si_no_hay_database_url():
    """La integración de Supabase en Vercel define POSTGRES_URL. Sin esto
    habría que copiar la misma cadena a mano en DATABASE_URL."""
    s = Settings(
        POSTGRES_URL="postgres://user:pass@pooler:6543/db",
        JWT_SECRET="un-secreto-de-desarrollo-cualquiera",
        DEBUG=True,
        _env_file=None,
    )
    assert s.DATABASE_URL == "postgresql://user:pass@pooler:6543/db"


def test_database_url_explicita_le_gana_a_la_de_la_integracion():
    s = Settings(
        DATABASE_URL="postgresql://user:pass@elegida:5432/db",
        POSTGRES_URL="postgresql://user:pass@pooler:6543/db",
        JWT_SECRET="un-secreto-de-desarrollo-cualquiera",
        DEBUG=True,
        _env_file=None,
    )
    assert "elegida" in s.DATABASE_URL


def test_sin_ninguna_url_falla():
    import pytest

    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(JWT_SECRET="x" * 40, DEBUG=True, _env_file=None)


def test_saca_el_parametro_supa_del_pooler_de_supabase():
    """La URL del pooler viene con `supa=base-pooler.x`, que psycopg2 no
    conoce: sin sacarlo corta con `invalid connection option "supa"`."""
    s = _settings(
        "postgresql://u:p@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
        "?sslmode=require&supa=base-pooler.x"
    )
    assert "supa=" not in s.DATABASE_URL
    assert s.DATABASE_URL.endswith("/postgres?sslmode=require")


def test_no_toca_una_url_sin_query():
    url = "postgresql://u:p@host:5432/db"
    assert _settings(url).DATABASE_URL == url
