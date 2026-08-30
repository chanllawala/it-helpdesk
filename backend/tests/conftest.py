import os
import tempfile

import pytest

# The engine is built from settings at import time, so the database has to be
# pointed somewhere disposable before anything under app/ is imported.
_TMP_DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ.setdefault("JWT_SECRET_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    """Every test starts from an empty schema, so ordering cannot matter."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def make_user(db):
    """Create a user with an arbitrary role.

    Registration deliberately refuses to grant privileged roles, so agents and
    admins are inserted directly rather than through the API.
    """

    def _make(email: str, role: UserRole = UserRole.USER, password: str = "password123"):
        user = User(
            email=email,
            full_name=email.split("@")[0].title(),
            hashed_password=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def login(client):
    def _login(email: str, password: str = "password123") -> dict:
        response = client.post(
            "/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login
