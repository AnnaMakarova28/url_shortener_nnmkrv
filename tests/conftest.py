import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# ВАЖНО: подменяем env до импорта app.main / settings
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["SECRET_KEY"] = "testsecret"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["BASE_URL"] = "http://testserver"

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import Base, get_db  # noqa: E402
from app.db import base  # noqa: F401, E402  # чтобы модели зарегистрировались
from app.main import app  # noqa: E402


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post(
        "/auth/register",
        json={"email": "owner@test.com", "password": "12345678"},
    )

    login_response = client.post(
        "/auth/login",
        data={"username": "owner@test.com", "password": "12345678"},
    )

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
