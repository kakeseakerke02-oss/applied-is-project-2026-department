"""pytest + TestClient: әр тест бөлек SQLite базасында орындалады."""

from decimal import Decimal
import importlib

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database.db import get_session, make_engine
from app.database.models import Criterion
from seed import seed


@pytest.fixture
def client(tmp_path, monkeypatch):
    main = importlib.import_module("app.main")
    engine = make_engine(tmp_path / "test.db", echo=False)
    seed(engine)

    def session_override():
        with Session(engine) as session:
            yield session

    # Lifespan да тек тест базасын ашады; негізгі database.db өзгермейді.
    monkeypatch.setattr(main, "init_db", lambda: None)
    previous = main.app.dependency_overrides.copy()
    main.app.dependency_overrides[get_session] = session_override
    try:
        with TestClient(main.app) as test_client:
            test_client.test_engine = engine
            yield test_client
    finally:
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(previous)
        engine.dispose()


@pytest.fixture
def payload():
    return {"discipline_id": 1, "author_id": 1, "title": "Автотест құралы",
            "tool_type": "Тест", "content": "SQL сұрақтары",
            "criteria": [{"description": "Дұрыс жауап", "max_score": "20.00"}]}


def test_get_list(client):
    response = client.get("/assessment-tools")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 5


def test_post_persists(client, payload):
    response = client.post("/assessment-tools", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == payload["title"]
    assert created["id"] > 0
    assert Decimal(created["total_score"]) == Decimal("20")
    assert client.get(f"/assessment-tools/{created['id']}").json() == created


@pytest.mark.parametrize("changes", [
    {"title": "   "}, {"id": 999}, {"author_id": -1},
    {"criteria": [{"description": "Балл", "max_score": -1}]},
])
def test_invalid_post_does_not_insert(client, payload, changes):
    response = client.post("/assessment-tools", json={**payload, **changes})
    assert response.status_code == 422
    assert len(client.get("/assessment-tools").json()) == 5


def test_duplicate_rolls_back(client, payload):
    assert client.post("/assessment-tools", json=payload).status_code == 201
    assert client.post("/assessment-tools", json=payload).status_code == 409
    assert len(client.get("/assessment-tools").json()) == 6


def test_missing_foreign_key(client, payload):
    assert client.post("/assessment-tools", json={**payload, "author_id": 99999}).status_code == 404
    assert len(client.get("/assessment-tools").json()) == 5


def test_patch_preserves_other_fields(client):
    before = client.get("/assessment-tools/1").json()
    response = client.patch("/assessment-tools/1", json={"title": "Жаңартылған атау"})
    assert response.status_code == 200
    assert response.json() == {**before, "title": "Жаңартылған атау"}
    assert client.patch("/assessment-tools/1", json={"title": None}).status_code == 422


def test_delete_cascades_and_missing_returns_404(client):
    assert client.delete("/assessment-tools/1").status_code == 204
    with Session(client.test_engine) as session:
        assert session.exec(select(Criterion).where(Criterion.assessment_tool_id == 1)).all() == []
    assert client.get("/assessment-tools/1").status_code == 404
    assert client.patch("/assessment-tools/1", json={"title": "Жоқ"}).status_code == 404
    assert client.delete("/assessment-tools/1").status_code == 404


def test_filters_and_injection_input(client):
    matches = client.get("/assessment-tools", params={"search": "sql", "min_score": 20, "max_score": 20})
    assert matches.status_code == 200
    assert [row["id"] for row in matches.json()] == [1]
    assert client.get("/assessment-tools", params={"search": "' OR 1=1 --"}).json() == []
    assert client.get("/assessment-tools", params={"min_score": 30, "max_score": 10}).status_code == 422
    assert len(client.get("/assessment-tools").json()) == 5
