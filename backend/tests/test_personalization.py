from datetime import datetime, timedelta, timezone

import pytest

from app.database import SessionLocal
from app.models import Category, Event


@pytest.fixture()
def seed(client):
    db = SessionLocal()
    konser, tiyatro, sergi = Category(name="konser"), Category(name="tiyatro"), Category(name="sergi")
    db.add_all([konser, tiyatro, sergi])
    db.flush()
    when = datetime.now(timezone.utc) + timedelta(days=3)
    events = [
        Event(title="Caz Gecesi", category_id=konser.id, start_date=when, price=250),
        Event(title="Hamlet", category_id=tiyatro.id, start_date=when, price=None),
    ]
    db.add_all(events)
    db.commit()
    ids = {"konser": konser.id, "tiyatro": tiyatro.id, "sergi": sergi.id, "events": [e.id for e in events]}
    db.close()
    return ids


@pytest.fixture()
def auth(client):
    res = client.post(
        "/api/auth/register", json={"email": "s@example.com", "password": "gizli1234", "name": "Seray"}
    )
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


def test_interests_set_and_onboarding(client, seed, auth):
    assert client.get("/api/users/me/interests", headers=auth).json()["data"] == []
    res = client.put(
        "/api/users/me/interests", json={"category_ids": [seed["konser"], seed["tiyatro"]]}, headers=auth
    )
    assert res.status_code == 200
    assert {i["name"] for i in res.json()["data"]} == {"konser", "tiyatro"}
    assert client.get("/api/users/me", headers=auth).json()["data"]["onboarding_done"] is True

    res = client.put("/api/users/me/interests", json={"category_ids": [seed["sergi"]]}, headers=auth)
    assert [i["name"] for i in res.json()["data"]] == ["sergi"]


def test_interests_unknown_category(client, seed, auth):
    res = client.put("/api/users/me/interests", json={"category_ids": [999]}, headers=auth)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "UNKNOWN_CATEGORY"


def test_favorites_flow(client, seed, auth):
    e1, e2 = seed["events"]
    assert client.post(f"/api/users/me/favorites/{e1}", headers=auth).status_code == 201
    client.post(f"/api/users/me/favorites/{e1}", headers=auth)  # tekrar eklemek sorun çıkarmaz
    client.post(f"/api/users/me/favorites/{e2}", headers=auth)
    res = client.get("/api/users/me/favorites", headers=auth).json()
    assert res["meta"]["total"] == 2
    assert {e["title"] for e in res["data"]} == {"Caz Gecesi", "Hamlet"}
    assert res["data"][0]["category"]["name"] in {"konser", "tiyatro"}

    assert client.delete(f"/api/users/me/favorites/{e1}", headers=auth).status_code == 204
    assert client.get("/api/users/me/favorites", headers=auth).json()["meta"]["total"] == 1


def test_favorite_unknown_event(client, seed, auth):
    res = client.post("/api/users/me/favorites/999", headers=auth)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_rating_create_and_update(client, seed, auth):
    e1 = seed["events"][0]
    assert client.post(f"/api/events/{e1}/rating", json={"rating": 4}, headers=auth).json()["data"]["rating"] == 4
    assert client.post(f"/api/events/{e1}/rating", json={"rating": 2}, headers=auth).json()["data"]["rating"] == 2
    assert client.post(f"/api/events/{e1}/rating", json={"rating": 6}, headers=auth).status_code == 422


def test_interactions(client, seed, auth):
    e1 = seed["events"][0]
    assert client.post("/api/interactions", json={"event_id": e1, "type": "click"}, headers=auth).status_code == 202
    assert client.post("/api/interactions", json={"event_id": e1, "type": "hack"}, headers=auth).status_code == 422
    assert client.post("/api/interactions", json={"event_id": e1, "type": "view"}).status_code == 401
