"""
Shared pytest fixtures for the Zomato Notes backend.

Two important things happen here:
1. Environment variables are set BEFORE importing the app, because
   `database.py` raises RuntimeError if DATABASE_URL is missing, and
   `ai_service.py` reads MOCK_AI at import time.
2. The real Supabase `get_db` dependency is swapped for an in-memory
   SQLite session, so tests never touch the production database.
"""

import os

# ── Force env BEFORE importing anything that reads database.py / main.py ─────
#    Using assignment (not setdefault) so tests stay hermetic: an ambient
#    SECRET_TOKEN or DATABASE_URL from the shell/CI cannot leak in.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_TOKEN"] = "test-secret"
os.environ["MOCK_AI"] = "1"            # avoid real Groq calls in tests
os.environ["AI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import Base, get_db

# ── Replace the 2.5-second background indexing task with a no-op so tests
#    that create notes stay fast (no asyncio.sleep delay). ──────────────────────
async def _noop_index_note(note_id: int):
    pass

main._index_note_background = _noop_index_note

# ── Test database: single in-memory SQLite connection shared across requests ──
#    StaticPool keeps one connection so tables created by the fixture persist
#    and are visible to every request in the test.
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Swap the real DB dependency for the test DB
main.app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Create a fresh schema before each test, drop it after — keeps tests
    isolated and order-independent."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    """FastAPI test client wired to the in-memory test database."""
    return TestClient(main.app)


# ── JWT helper fixture ────────────────────────────────────────────────────────

TEST_PASSWORD = "testpass123"


def _register_and_login(client, email="fixture@test.com", name="Fixture User"):
    """Register a user and return (user_dict, jwt_token)."""
    res = client.post("/users", json={"name": name, "email": email, "password": TEST_PASSWORD})
    assert res.status_code == 201, f"User creation failed: {res.json()}"
    user = res.json()

    login = client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200, f"Login failed: {login.json()}"
    token = login.json()["access_token"]
    return user, token


@pytest.fixture()
def auth_client(client):
    """
    Returns a helper object with:
      .client  — the TestClient
      .user    — the registered user dict
      .token   — the JWT access token string
      .headers — {"Authorization": "Bearer <token>"} ready for use
    """
    user, token = _register_and_login(client)

    class _Auth:
        pass

    a = _Auth()
    a.client  = client
    a.user    = user
    a.token   = token
    a.headers = {"Authorization": f"Bearer {token}"}
    return a
