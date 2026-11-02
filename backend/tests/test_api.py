import uuid

import pytest
from sqlalchemy import func, select

from app.models import ErrorType


@pytest.fixture
def type_name():
    """error_types 是全域表，每個測試用唯一名稱，避免受資料庫既有資料影響。"""
    return f"t-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample(type_name):
    return {
        "original_text": "I go to school yesterday.",
        "corrected_text": "I went to school yesterday.",
        "explanation": "Past time marker requires past tense.",
        "source": "skill",
        "errors": [{"error_type": type_name, "error_snippet": "go", "suggestion": "went"}],
    }


def count_type(db, name):
    return db.scalar(select(func.count()).select_from(ErrorType).where(ErrorType.name == name))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_missing_api_key_is_401(client, sample):
    assert client.get("/error-types").status_code == 401
    assert client.post("/sentences", json=sample).status_code == 401


def test_wrong_api_key_is_401(client):
    assert client.get("/error-types", headers={"X-API-Key": "nope"}).status_code == 401


def test_post_sentence_creates_new_error_type(client, auth, db, sample, type_name):
    assert count_type(db, type_name) == 0

    r = client.post("/sentences", json=sample, headers=auth)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["source"] == "skill"
    assert body["is_dismissed"] is False
    assert body["errors"][0]["error_type"]["name"] == type_name

    names = [t["name"] for t in client.get("/error-types", headers=auth).json()]
    assert type_name in names
    assert count_type(db, type_name) == 1


def test_existing_error_type_is_reused(client, auth, db, sample, type_name):
    client.post("/sentences", json=sample, headers=auth)
    second = {
        **sample,
        "original_text": "She go home.",
        "corrected_text": "She went home.",
        # 大小寫與前後空白不同，仍應視為同一類型
        "errors": [{"error_type": f" {type_name.upper()} ", "error_snippet": "go", "suggestion": "went"}],
    }
    r = client.post("/sentences", json=second, headers=auth)
    assert r.status_code == 201
    assert r.json()["errors"][0]["error_type"]["name"] == type_name
    assert count_type(db, type_name) == 1


def test_list_get_and_stats(client, auth, sample, type_name):
    created = client.post("/sentences", json=sample, headers=auth).json()

    listed = client.get("/sentences", headers=auth).json()
    assert [s["id"] for s in listed] == [created["id"]]  # tester 使用者只有這一筆
    assert client.get("/sentences", params={"error_type": type_name}, headers=auth).json()[0]["id"] == created["id"]
    assert client.get("/sentences", params={"error_type": "no-such-type"}, headers=auth).json() == []

    assert client.get(f"/sentences/{created['id']}", headers=auth).status_code == 200
    assert client.get("/sentences/999999", headers=auth).status_code == 404

    stats = client.get("/stats/errors", headers=auth).json()
    assert stats == [
        {"error_type_id": created["errors"][0]["error_type"]["id"], "error_type": type_name, "count": 1}
    ]
