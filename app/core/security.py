from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hashea una contraseña."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    """Crea un token de acceso JWT para el sujeto indicado."""
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        settings.jwt_secret.get_secret_value(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, object]:
    """Decodifica y valida un token de acceso JWT."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[ALGORITHM],
    )
