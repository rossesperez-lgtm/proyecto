"""Create users, roles, and permissions.

Revision ID: 0001_initial
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear el esquema inicial de usuarios, roles y permisos."""
    # Crear la tabla de usuarios y su índice único de correo electrónico.

    # Pylint no detecta las operaciones que Alembic expone dinámicamente.
    # pylint: disable=no-member
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("name", name="uq_permissions_name"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    roles = sa.table("roles", sa.column("id", sa.Integer), sa.column("name", sa.String))
    permissions = sa.table(
        "permissions", sa.column("id", sa.Integer), sa.column("name", sa.String)
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )
    op.bulk_insert(roles, [{"name": "user"}, {"name": "admin"}])
    op.bulk_insert(
        permissions,
        [
            {"name": "users:read"},
            {"name": "users:roles:assign"},
        ],
    )
    bind = op.get_bind()
    role_ids = dict(bind.execute(sa.select(roles.c.name, roles.c.id)).all())
    permission_ids = dict(
        bind.execute(sa.select(permissions.c.name, permissions.c.id)).all()
    )
    op.bulk_insert(
        role_permissions,
        [
            {
                "role_id": role_ids["admin"],
                "permission_id": permission_ids["users:read"],
            },
            {
                "role_id": role_ids["admin"],
                "permission_id": permission_ids["users:roles:assign"],
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
