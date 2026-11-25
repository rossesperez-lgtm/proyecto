from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Role, User
from app.schemas import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["authentication"])


# /register endpoint for user registration
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Registra un usuario nuevo y devuelve su perfil público."""
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user_role = db.scalar(select(Role).where(Role.name == "user"))
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Roles are not initialized; run database migrations",
        )

    user = User(
        email=email, hashed_password=hash_password(payload.password), roles=[user_role]
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None
    db.refresh(user)
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        roles=[user_role.name],
        created_at=user.created_at,
    )


# /token endpoint for user login
@router.post("/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Autentica al usuario y devuelve un token de acceso."""
    email = form.username.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return Token(access_token=create_access_token(str(user.id)))
