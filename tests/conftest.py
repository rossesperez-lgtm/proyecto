import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-that-is-long-enough-for-tests")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Permission, Role

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client():
    """Proporciona un cliente de pruebas con una base de datos en memoria aislada."""
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        user_role = Role(name="user")
        admin_role = Role(
            name="admin",
            permissions=[
                Permission(name="users:read"),
                Permission(name="users:roles:assign"),
            ],
        )
        db.add_all([user_role, admin_role])
        db.commit()

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.app.state.session_factory = TestingSessionLocal
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
