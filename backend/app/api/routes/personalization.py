"""İlgi alanları, favoriler, puanlama ve etkileşim uçları (Seray)."""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.database import get_db
from app.models import Category, Event, Favorite, Interaction, Interest, Rating, User
from app.schemas import (
    Envelope,
    EventSummaryOut,
    InteractionIn,
    InterestOut,
    InterestsIn,
    PagedEnvelope,
    PageMeta,
    RatingIn,
    RatingOut,
)

router = APIRouter(tags=["personalization"])


def _get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise ApiError(404, "EVENT_NOT_FOUND", "Etkinlik bulunamadı.")
    return event


# --- İlgi alanları (cold start) ---

def _interests_of(db: Session, user: User) -> list[InterestOut]:
    rows = db.execute(
        select(Category, Interest.weight)
        .join(Interest, Interest.category_id == Category.id)
        .where(Interest.user_id == user.id)
        .order_by(Interest.weight.desc(), Category.name)
    ).all()
    return [InterestOut(id=c.id, name=c.name, weight=w) for c, w in rows]


@router.get("/users/me/interests", response_model=Envelope[list[InterestOut]])
def get_interests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return Envelope(data=_interests_of(db, user))


@router.put("/users/me/interests", response_model=Envelope[list[InterestOut]])
def set_interests(body: InterestsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = set(body.category_ids)
    found = set(db.scalars(select(Category.id).where(Category.id.in_(ids))))
    if missing := ids - found:
        raise ApiError(422, "UNKNOWN_CATEGORY", f"Bilinmeyen kategori: {sorted(missing)}")

    # Önceden öğrenilmiş ağırlıklar korunur, seçimden çıkarılanlar silinir.
    existing = {i.category_id: i for i in db.scalars(select(Interest).where(Interest.user_id == user.id))}
    for cid, interest in existing.items():
        if cid not in ids:
            db.delete(interest)
    for cid in ids - existing.keys():
        db.add(Interest(user_id=user.id, category_id=cid, weight=1.0))

    user.onboarding_done = True
    db.commit()
    return Envelope(data=_interests_of(db, user))


# --- Favoriler ---

@router.get("/users/me/favorites", response_model=PagedEnvelope[list[EventSummaryOut]])
def list_favorites(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id))
    events = db.scalars(
        select(Event)
        .join(Favorite, Favorite.event_id == Event.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return PagedEnvelope(
        data=[EventSummaryOut.model_validate(e) for e in events],
        meta=PageMeta(total=total, page=page, limit=limit),
    )


@router.post("/users/me/favorites/{event_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_event_or_404(db, event_id)
    if db.get(Favorite, (user.id, event_id)) is None:
        db.add(Favorite(user_id=user.id, event_id=event_id))
        db.commit()
    return {"data": {"event_id": event_id, "favorite": True}}


@router.delete("/users/me/favorites/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(delete(Favorite).where(Favorite.user_id == user.id, Favorite.event_id == event_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Puanlama ---

@router.post("/events/{event_id}/rating", response_model=Envelope[RatingOut])
def rate_event(
    event_id: int, body: RatingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _get_event_or_404(db, event_id)
    rating = db.get(Rating, (user.id, event_id))
    if rating is None:
        db.add(Rating(user_id=user.id, event_id=event_id, rating=body.rating))
    else:
        rating.rating = body.rating
    db.commit()
    return Envelope(data=RatingOut(event_id=event_id, rating=body.rating))


# --- Örtük geri bildirim ---

@router.post("/interactions", status_code=status.HTTP_202_ACCEPTED)
def log_interaction(body: InteractionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_event_or_404(db, body.event_id)
    db.add(Interaction(user_id=user.id, event_id=body.event_id, type=body.type))
    db.commit()
    return Response(status_code=status.HTTP_202_ACCEPTED)
