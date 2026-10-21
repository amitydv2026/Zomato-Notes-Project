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

# ── Set env BEFORE importing anything that reads database.py / main.py ───────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_TOKEN", "test-secret")
os.environ.setdefault("MOCK_AI", "1")          # avoid real Groq calls in tests
os.environ.setdefault("AI_API_KEY", "test-key")

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
