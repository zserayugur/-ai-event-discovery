"""Öneri motoru (Seray).

İçerik tabanlı ilk sürüm. Kullanıcının kategori tercihi şu sinyallerden hesaplanır:
  - Seçtiği ilgi alanları (interests.weight)
  - Favorilediği, puanladığı, tıkladığı etkinliklerin kategorileri
Yaklaşan etkinlikler bu tercih + yakınlık + popülerlik ile puanlanır.
Hiç sinyal yoksa (cold start) popüler ve yakın tarihli etkinlikler döner.

İş birlikçi filtreleme ("bunu sevenler şunu da sevdi") ikinci adımda eklenecek.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Event, Favorite, Interaction, Interest, Rating, User

# Sinyal ağırlıkları: bir kategoriye olan ilgiye ne kadar katkı yaptıkları
INTEREST_WEIGHT = 3.0
FAVORITE_WEIGHT = 2.0
RATING_WEIGHT = 0.8          # (puan - 3) ile çarpılır: 5 -> +1.6, 1 -> -1.6
INTERACTION_WEIGHTS = {"view": 0.1, "click": 0.3, "ticket_click": 1.0, "dismiss": -0.5}

# Etkinlik puanındaki payları
PREFERENCE_SHARE = 0.7
RECENCY_SHARE = 0.2
POPULARITY_SHARE = 0.1
RECENCY_HORIZON_DAYS = 30


@dataclass
class Recommendation:
    event: Event
    score: float
    reason: str


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def category_preferences(db: Session, user: User) -> dict[int, float]:
    prefs: dict[int, float] = defaultdict(float)

    for i in db.scalars(select(Interest).where(Interest.user_id == user.id)):
        prefs[i.category_id] += INTEREST_WEIGHT * i.weight

    fav_rows = db.execute(
        select(Event.category_id).join(Favorite, Favorite.event_id == Event.id).where(Favorite.user_id == user.id)
    )
    for (cid,) in fav_rows:
        prefs[cid] += FAVORITE_WEIGHT

    rating_rows = db.execute(
        select(Event.category_id, Rating.rating).join(Rating, Rating.event_id == Event.id).where(Rating.user_id == user.id)
    )
    for cid, r in rating_rows:
        prefs[cid] += RATING_WEIGHT * (r - 3)

    inter_rows = db.execute(
        select(Event.category_id, Interaction.type)
        .join(Interaction, Interaction.event_id == Event.id)
        .where(Interaction.user_id == user.id)
    )
    for cid, t in inter_rows:
        prefs[cid] += INTERACTION_WEIGHTS.get(t, 0)

    return {cid: v for cid, v in prefs.items() if v > 0}


def _popularity(db: Session, event_ids: list[int]) -> dict[int, int]:
    if not event_ids:
        return {}
    rows = db.execute(
        select(Favorite.event_id, func.count()).where(Favorite.event_id.in_(event_ids)).group_by(Favorite.event_id)
    )
    return dict(rows.all())


def _excluded_event_ids(db: Session, user: User | None) -> set[int]:
    """Kullanıcının zaten favorilediği veya 'ilgilenmiyorum' dediği etkinlikler önerilmez."""
    if user is None:
        return set()
    favs = set(db.scalars(select(Favorite.event_id).where(Favorite.user_id == user.id)))
    dismissed = set(
        db.scalars(select(Interaction.event_id).where(Interaction.user_id == user.id, Interaction.type == "dismiss"))
    )
    return favs | dismissed


def recommend(db: Session, user: User | None, limit: int = 20) -> list[Recommendation]:
    now = datetime.now(timezone.utc)
    excluded = _excluded_event_ids(db, user)
    candidates = [
        e
        for e in db.scalars(select(Event).where(Event.start_date >= now).order_by(Event.start_date))
        if e.id not in excluded and _aware(e.start_date) >= now
    ]
    if not candidates:
        return []

    prefs = category_preferences(db, user) if user else {}
    max_pref = max(prefs.values(), default=0)
    popularity = _popularity(db, [e.id for e in candidates])
    max_pop = max(popularity.values(), default=0)

    results = []
    for e in candidates:
        days_left = (_aware(e.start_date) - now).total_seconds() / 86400
        recency = max(0.0, 1 - days_left / RECENCY_HORIZON_DAYS)
        pop = popularity.get(e.id, 0) / max_pop if max_pop else 0.0
        pref = prefs.get(e.category_id, 0) / max_pref if max_pref else 0.0

        if max_pref:  # kişiselleştirilmiş
            score = PREFERENCE_SHARE * pref + RECENCY_SHARE * recency + POPULARITY_SHARE * pop
            if pref > 0:
                reason = f"{e.category.name.capitalize()} ilgin nedeniyle"
            elif pop > 0:
                reason = "Şu sıralar popüler"
            else:
                reason = "Yakında gerçekleşecek"
        else:  # cold start
            score = 0.6 * pop + 0.4 * recency
            reason = "Şu sıralar popüler" if pop > 0 else "Yakında gerçekleşecek"

        results.append(Recommendation(event=e, score=round(score, 4), reason=reason))

    results.sort(key=lambda r: (-r.score, _aware(r.event.start_date)))
    return results[:limit]
