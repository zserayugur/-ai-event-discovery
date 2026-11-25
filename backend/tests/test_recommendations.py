from datetime import datetime, timedelta, timezone

import pytest

from app.database import SessionLocal
from app.models import Category, Event


@pytest.fixture()
def seed(client):
    db = SessionLocal()
    konser, tiyatro = Category(name="konser"), Category(name="tiyatro")
    db.add_all([konser, tiyatro])
    db.flush()
    now = datetime.now(timezone.utc)
    ev = {
        "caz": Event(title="Caz Gecesi", category_id=konser.id, start_date=now + timedelta(days=10)),
        "rock": Event(title="Rock Konseri", category_id=konser.id, start_date=now + timedelta(days=20)),
        "hamlet": Event(title="Hamlet", category_id=tiyatro.id, start_date=now + timedelta(days=1)),
        "gecmis": Event(title="Geçmiş Konser", category_id=konser.id, start_date=now - timedelta(days=2)),
    }
    db.add_all(ev.values())
    db.commit()
    ids = {k: e.id for k, e in ev.items()} | {"konser": konser.id, "tiyatro": tiyatro.id}
    db.close()
    return ids


def make_user(client, email):
    res = client.post("/api/auth/register", json={"email": email, "password": "gizli1234", "name": "X"})
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


def titles(res):
    return [r["event"]["title"] for r in res.json()["data"]]


def test_cold_start_anonymous(client, seed):
    res = client.get("/api/recommendations")
    assert res.status_code == 200
    t = titles(res)
    assert "Geçmiş Konser" not in t
    assert t[0] == "Hamlet"  # hiç sinyal yokken en yakın tarihli öne çıkar


def test_cold_start_uses_popularity(client, seed):
    for i in range(3):
        client.post(f"/api/users/me/favorites/{seed['rock']}", headers=make_user(client, f"u{i}@x.com"))
    res = client.get("/api/recommendations")
    assert titles(res)[0] == "Rock Konseri"
    assert res.json()["data"][0]["reason"] == "Şu sıralar popüler"


def test_interests_drive_recommendations(client, seed):
    h = make_user(client, "seray@x.com")
    client.put("/api/users/me/interests", json={"category_ids": [seed["konser"]]}, headers=h)
    data = client.get("/api/recommendations", headers=h).json()["data"]
    assert data[0]["event"]["title"] in {"Caz Gecesi", "Rock Konseri"}
    assert data[0]["reason"] == "Konser ilgin nedeniyle"
    assert data[-1]["event"]["title"] == "Hamlet"


def test_favorited_and_dismissed_are_excluded(client, seed):
    h = make_user(client, "seray@x.com")
    client.post(f"/api/users/me/favorites/{seed['caz']}", headers=h)
    client.post("/api/interactions", json={"event_id": seed["hamlet"], "type": "dismiss"}, headers=h)
    t = titles(client.get("/api/recommendations", headers=h))
    assert "Caz Gecesi" not in t and "Hamlet" not in t
    assert t == ["Rock Konseri"]


def test_low_rating_reduces_category(client, seed):
    h = make_user(client, "seray@x.com")
    client.put("/api/users/me/interests", json={"category_ids": [seed["tiyatro"]]}, headers=h)
    client.post(f"/api/events/{seed['caz']}/rating", json={"rating": 5}, headers=h)
    client.post(f"/api/events/{seed['caz']}/rating", json={"rating": 5}, headers=h)
    data = client.get("/api/recommendations", headers=h).json()["data"]
    assert data[0]["event"]["title"] == "Hamlet"
