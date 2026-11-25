from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Tablas de asociación para relaciones de muchos a muchos entre usuarios, roles y permisos.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    """Modelo de SQLAlchemy que representa a un usuario de la aplicación."""

    # pylint: disable=too-few-public-methods
    __tablename__ = "users"

    # Identificador único del usuario.
    # Mapped es un tipo genérico que indica que el atributo es una columna mapeada en la base de datos.
    # que significa que el atributo es una columna mapeada en la base de datos?
    # significa que el atributo de la clase User está vinculado a una columna específica en la tabla
    # "users" de la base de datos.
    # Esto permite que SQLAlchemy gestione automáticamente la persistencia y recuperación de datos
    # entre la aplicación y la base de datos, facilitando el trabajo con objetos Python en lugar de
    # escribir consultas SQL manualmente.
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles, back_populates="users", lazy="selectin"
    )


class Role(Base):
    """Modelo de SQLAlchemy que representa un rol de la aplicación."""

    # pylint: disable=too-few-public-methods
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    users: Mapped[list[User]] = relationship(
        secondary=user_roles, back_populates="roles"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )


class Permission(Base):
    """Modelo de SQLAlchemy que representa un permiso de la aplicación."""

    # pylint: disable=too-few-public-methods
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )
