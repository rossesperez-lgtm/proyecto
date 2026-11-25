"""Database session and engine configuration."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Importa la configuración central de la aplicación.
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Proporciona una sesión de base de datos y la cierra al finalizar."""
    with SessionLocal() as session:
        yield session
