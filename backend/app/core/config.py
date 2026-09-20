from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_SECRETS = {"changeme", "secret", "your-secret-key", "supersecret", ""}


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:3000"
    # Falso por defecto: si en producción alguien se olvida de definirlo,
    # la app arranca cerrada (sin /docs y con el secreto validado) en vez
    # de abierta. En local se prende desde el .env.
    DEBUG: bool = False
    # Storage de fotos, cualquier servicio S3-compatible. En producción es
    # Supabase Storage; la URL pública es la del bucket, sin barra final.
    STORAGE_ENDPOINT_URL: str = ""
    STORAGE_REGION: str = "auto"
    STORAGE_ACCESS_KEY_ID: str = ""
    STORAGE_SECRET_ACCESS_KEY: str = ""
    STORAGE_BUCKET: str = ""
    STORAGE_PUBLIC_URL: str = ""

    @model_validator(mode="after")
    def normalizar_database_url(self) -> "Settings":
        """Railway y otros proveedores entregan la URL con el esquema
        `postgres://`, que SQLAlchemy 2.0 ya no reconoce. Normalizarlo acá
        evita un error críptico en el arranque."""
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql://", 1
            )
        return self

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if not self.DEBUG:
            if self.JWT_SECRET.lower() in _INSECURE_SECRETS:
                raise ValueError(
                    "JWT_SECRET no puede ser un valor por defecto en producción. "
                    "Configura una clave segura en las variables de entorno."
                )
            if len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "JWT_SECRET debe tener al menos 32 caracteres en producción."
                )
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL es requerida.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        # Un .env viejo con variables que ya no existen (las R2_* de antes
        # de pasar a STORAGE_*) no debe impedir que la app arranque.
        extra = "ignore"


settings = Settings()
