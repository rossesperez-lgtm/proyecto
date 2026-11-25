from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Devuelve el usuario autenticado o lanza un error de autorización."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        user_id = int(subject) if isinstance(subject, str) else None
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise unauthorized from None

    if user_id is None:
        raise unauthorized

    user = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_permission(permission_name: str) -> Callable:
    """Crea una dependencia que exige un permiso específico al usuario."""

    def permission_checker(user: User = Depends(get_current_user)) -> User:
        """Comprueba que el usuario autenticado tenga el permiso requerido."""
        permissions = {
            permission.name for role in user.roles for permission in role.permissions
        }
        if permission_name not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return permission_checker
