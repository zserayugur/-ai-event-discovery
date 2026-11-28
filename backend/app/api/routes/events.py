
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.schemas import EventCreate, EventResponse
from app.database import get_db
from app.models import Event, Venue
router = APIRouter(prefix="/events", tags=["Events"])


@router.get("")
def get_events(
    search: str | None = None,
    category: str | None = None,
    city: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):

    query = db.query(Event)

    if search:
        query = query.filter(
            Event.title.ilike(f"%{search}%")
        )

    if category:
        query = query.filter(
            Event.category.has(name=category)
        )

    if city:
        query = query.filter(
            Event.venue.has(Venue.city.ilike(city))
        )


    total = query.count()

    events = (
     query
     .order_by(Event.id.asc())
     .offset((page - 1) * limit)
     .limit(limit)
     .all()
     )






    return {
        "data": [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "category": event.category.name,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "venue_id": event.venue_id,
            }
            for event in events
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    }



@router.get("/{event_id}")
def get_event_detail(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Etkinlik bulunamadi."
        )

    return {
        "data": {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "category": event.category.name,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "price": event.price,
            "source": event.source,
            "source_url": event.source_url,
            "image_url": event.image_url,
            "venue_id": event.venue_id,
            "venue": {
                "id": event.venue.id,
                "name": event.venue.name,
                "city": event.venue.city,
                "address": event.venue.address
            } if event.venue else None
        }
    }


@router.post("", response_model=EventResponse, status_code=201)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    from app.models import Category

    category = db.query(Category).filter(
        Category.id == event_data.category_id
    ).first()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Belirtilen kategori bulunamadi."
        )

    if event_data.venue_id is not None:
        venue = db.query(Venue).filter(
            Venue.id == event_data.venue_id
        ).first()

        if venue is None:
            raise HTTPException(
                status_code=404,
                detail="Belirtilen mekan bulunamadi."
            )

    if (
        event_data.end_date is not None
        and event_data.end_date <= event_data.start_date
    ):
        raise HTTPException(
            status_code=422,
            detail="Bitis tarihi baslangic tarihinden sonra olmalidir."
        )

    new_event = Event(**event_data.model_dump())

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event
