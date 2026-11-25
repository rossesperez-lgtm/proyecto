import argparse
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Role, User


def create_admin(email: str) -> None:
    """Crea un usuario administrador o asigna el rol de administrador a un usuario existente."""
    email = email.lower()
    password = getpass("Admin password (minimo 12 caracteres): ")
    confirmation = getpass("Confirmar password: ")
    if password != confirmation:
        raise SystemExit("Passwords no coinciden.")
    if len(password) < 12 or len(password) > 128:
        raise SystemExit("Password  debe contener entre 12 y 128 caracteres.")

    with SessionLocal() as db:
        role = db.scalar(select(Role).where(Role.name == "admin"))
        if role is None:
            raise SystemExit(
                "Admin rol no encontrado. Ejecutar `alembic upgrade head` primero."
            )
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email, hashed_password=hash_password(password), roles=[role]
            )
            db.add(user)
        elif role not in user.roles:
            user.roles.append(role)
        db.commit()
    print(f"Admin rol asignado a {email}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comandos de mantenimiento de la API de autenticación"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_admin_parser = subparsers.add_parser(
        "create-admin", help="Crear o promover un admin"
    )
    create_admin_parser.add_argument("email")
    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.email)


if __name__ == "__main__":
    main()
