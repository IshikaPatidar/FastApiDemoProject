from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..fast2 import app2
from ..routers.todos import get_db, get_current_user
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from ..models import Todos


SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {'username': 'test', 'id': 4, 'user_role': 'admin'}


app2.dependency_overrides[get_db] = override_get_db()
app2.dependency_overrides[get_current_user] = override_get_current_user()

client = TestClient(app2)


@pytest.fixture()
def test_todo():
    todo = Todos(
        title="Something",
        description="Some Description",
        priority=5,
        complete=False,
        owner_id=4
    )

    db=TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()


def test_read_all_authenticated(test_todo):
    response = client.get("/todo/1")
    print(response)
    assert response.status_code == status.HTTP_200_OK
