from app.core.security import create_access_token, hash_password
from app.models import Role, User


def test_register_login_and_read_profile(client):
    """Prueba el registro, inicio de sesión y lectura del perfil del usuario actual."""

    registration = client.post(
        "/auth/register",
        json={"email": "Person@example.com", "password": "a-strong-password"},
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "person@example.com"
    assert registration.json()["roles"] == ["user"]

    login = client.post(
        "/auth/token",
        data={"username": "person@example.com", "password": "a-strong-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    profile = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "person@example.com"


def test_regular_user_cannot_list_users(client):
    """Prueba que un usuario normal no puede listar otros usuarios."""

    client.post(
        "/auth/register",
        json={"email": "person@example.com", "password": "a-strong-password"},
    )
    login = client.post(
        "/auth/token",
        data={"username": "person@example.com", "password": "a-strong-password"},
    )

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 403


def test_duplicate_registration_is_rejected(client):
    """Prueba que no se permite registrar dos veces el mismo correo."""

    payload = {"email": "person@example.com", "password": "a-strong-password"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_admin_can_list_users_and_assign_role(client):
    """Prueba que un administrador puede listar usuarios y asignar roles."""

    with client.app.state.session_factory() as db:
        user_role = db.query(Role).filter_by(name="user").one()
        admin_role = db.query(Role).filter_by(name="admin").one()
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("another-strong-password"),
            roles=[admin_role],
        )
        regular_user = User(
            email="person@example.com",
            hashed_password=hash_password("a-strong-password"),
            roles=[user_role],
        )
        db.add_all([admin, regular_user])
        db.commit()
        db.refresh(admin)
        db.refresh(regular_user)
        user_id = regular_user.id
        token = create_access_token(str(admin.id))

    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/users", headers=headers).status_code == 200
    response = client.put(
        f"/users/{user_id}/role",
        headers=headers,
        json={"role": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["roles"] == ["admin"]
