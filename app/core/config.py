from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    database_url: str
    jwt_secret: SecretStr = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación."""
    return Settings()
