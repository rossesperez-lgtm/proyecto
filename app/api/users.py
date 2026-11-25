from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models import Role, User
from app.schemas import RoleAssignment, UserRead

router = APIRouter(prefix="/users", tags=["users"])


def serialize_user(user: User) -> UserRead:
    """Serializa un modelo de usuario al esquema público de respuesta."""
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user)) -> UserRead:
    """Devuelve la información del usuario autenticado."""
    return serialize_user(user)


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(require_permission("users:read"))],
)
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    """Devuelve la lista de usuarios registrados."""
    users = db.scalars(
        select(User).options(selectinload(User.roles)).order_by(User.id)
    ).all()
    return [serialize_user(user) for user in users]


@router.put(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_permission("users:roles:assign"))],
)
def assign_role(
    user_id: int,
    payload: RoleAssignment,
    db: Session = Depends(get_db),
) -> UserRead:
    """Asigna al usuario el rol indicado."""
    user = db.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    role = db.scalar(select(Role).where(Role.name == payload.role))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    user.roles = [role]
    db.commit()
    db.refresh(user)
    return serialize_user(user)
