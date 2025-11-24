import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ARENA_DATABASE_URL", "sqlite:///./test_arena.db")

from app.config import get_settings

# Ensure settings reflect the test database
get_settings.cache_clear()  # type: ignore[attr-defined]

from app.database import engine
from app.main import app
from app.models import Base

TEST_DB_PATH = Path(engine.url.database or "test_arena.db")


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
