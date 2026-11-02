"""每個測試跑在一個外層交易裡，結束後 rollback，資料庫不會留下測試資料。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.main import app
from app.models import User

TEST_API_KEY = "test-key-conftest"


@pytest.fixture
def db():
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    session.add(User(name="tester", api_key=TEST_API_KEY))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"X-API-Key": TEST_API_KEY}
