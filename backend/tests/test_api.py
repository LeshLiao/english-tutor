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


def test_keyword_search(client, auth, sample):
    created = client.post("/sentences", json=sample, headers=auth).json()
    client.post("/sentences", json={**sample, "original_text": "She like cats.", "corrected_text": "She likes cats.", "errors": []}, headers=auth)

    hits = client.get("/sentences", params={"q": "SCHOOL"}, headers=auth).json()  # 不分大小寫
    assert [s["id"] for s in hits] == [created["id"]]
    assert client.get("/sentences", params={"q": "went"}, headers=auth).json()[0]["id"] == created["id"]  # 比對修正句
    assert client.get("/sentences", params={"q": "zzz-nothing"}, headers=auth).json() == []


def test_dismiss_excludes_from_list_and_stats(client, auth, sample, type_name):
    created = client.post("/sentences", json=sample, headers=auth).json()
    assert client.get("/stats/errors", headers=auth).json()[0]["count"] == 1

    r = client.patch(f"/sentences/{created['id']}", json={"is_dismissed": True}, headers=auth)
    assert r.status_code == 200
    assert r.json()["is_dismissed"] is True

    assert client.get("/sentences", headers=auth).json() == []
    assert [s["id"] for s in client.get("/sentences", params={"include_dismissed": True}, headers=auth).json()] == [created["id"]]
    assert client.get("/stats/errors", headers=auth).json() == []
    assert client.get("/stats/trend", headers=auth).json() == []

    # 取消標記後恢復
    client.patch(f"/sentences/{created['id']}", json={"is_dismissed": False}, headers=auth)
    assert client.get("/stats/errors", headers=auth).json()[0]["error_type"] == type_name

    assert client.patch("/sentences/999999", json={"is_dismissed": True}, headers=auth).status_code == 404
    assert client.patch(f"/sentences/{created['id']}", json={}, headers=auth).status_code == 422


def test_delete_removes_sentence_errors_and_stats(client, auth, sample, type_name):
    created = client.post("/sentences", json=sample, headers=auth).json()
    assert client.get(f"/sentences/{created['id']}", headers=auth).status_code == 200

    r = client.delete(f"/sentences/{created['id']}", headers=auth)
    assert r.status_code == 204
    assert r.content == b""

    assert client.get(f"/sentences/{created['id']}", headers=auth).status_code == 404
    assert client.get("/sentences", params={"include_dismissed": True}, headers=auth).json() == []
    assert client.get("/stats/errors", headers=auth).json() == []

    # 再刪一次或刪不存在的 → 404；沒帶 key → 401
    assert client.delete(f"/sentences/{created['id']}", headers=auth).status_code == 404
    assert client.delete(f"/sentences/{created['id']}").status_code == 401


def test_trend_groups_by_day_and_week(client, auth, sample):
    client.post("/sentences", json=sample, headers=auth)  # 1 error
    client.post("/sentences", json={**sample, "original_text": "It is correct.", "corrected_text": "It is correct.", "errors": []}, headers=auth)  # 0 errors

    day = client.get("/stats/trend", headers=auth).json()
    assert len(day) == 1
    assert day[0]["sentence_count"] == 2
    assert day[0]["error_count"] == 1

    week = client.get("/stats/trend", params={"interval": "week"}, headers=auth).json()
    assert len(week) == 1 and week[0]["sentence_count"] == 2
    assert client.get("/stats/trend", params={"interval": "month"}, headers=auth).status_code == 422


def test_cors_allows_vite_dev_server(client):
    r = client.options(
        "/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
