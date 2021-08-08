# -*- coding: utf-8 -*-
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.db.base_class import Base  # noqa: F401
from app.db.session import engine, SessionLocal
from app.main import app
from app.db.init_db import init_db

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
init_db(SessionLocal())

def pytest_configure(config):
    pass


@pytest.fixture(scope="session")
def db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client() -> Generator:
    yield TestClient(app)
