from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Esquema para crear un usuario."""

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserRead(BaseModel):
    """Esquema para consultar un usuario."""

    id: int
    email: EmailStr
    is_active: bool
    roles: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Esquema para representar un token de acceso."""

    access_token: str
    token_type: str = "bearer"


class RoleAssignment(BaseModel):
    """Esquema para asignar un rol a un usuario."""

    role: str = Field(min_length=1, max_length=50)
